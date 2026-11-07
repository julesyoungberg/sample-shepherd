#!/usr/bin/env python3
"""Report on a Fourier build: category counts, what was left out and why, folder sizes,
and anything a Digitakt II render might not load.

Reads only: the master's manifest.json, Fourier's database (read-only) and why logs, and
the render folders. Writes CSV + Markdown into --out (nothing with --dry-run).

  . ~/sample-work/fourier.env
  python scripts/build_report.py --out reports/phase1 [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sys
from pathlib import Path

import duckdb
import soundfile as sf

W = Path.home() / "sample-work"
FOLDER_LIMIT = 50
# Digitakt II facts used below: native format 16-bit / 48 kHz, mono or stereo (manual p.73);
# 400 MB of samples per project (p.17). No per-file length limit is documented: the 66 s
# figure is the max *sampling* time (p.68), used here only as a "long file" flag.
DT_RATE, DT_BITS, DT_LONG_S, DT_PROJECT_MB = 48000, 16, 66.0, 400


def why_reasons(home: Path, master: Path) -> dict[int, list[tuple[str, str, object]]]:
    sys.path.insert(0, str(W / "vendor/fourier-samples/src"))
    from fourier.packs import why_log  # noqa: E402  (only for the folder key)
    d = home / "why" / why_log.master_key(master)
    out: dict[int, list] = collections.defaultdict(list)
    for f in sorted(d.glob("*.json")):
        doc = json.loads(f.read_text())
        for reason, ids in (doc.get("out") or {}).items():
            for sid, detail in ids.items():
                out[int(sid)].append((doc["category"], reason, detail))
    return out


def walk_render(root: Path):
    for dp, _, fs in os.walk(root):
        for n in fs:
            if n.lower().endswith(".wav"):
                p = Path(dp) / n
                yield p, p.relative_to(root)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--master", default=str(W / "out/master"))
    ap.add_argument("--renders", default=str(W / "out/renders"))
    ap.add_argument("--home", default=os.environ.get("FOURIER_HOME", str(W / "fourier-home")))
    ap.add_argument("--digitakt", default="digitakt_2_50", help="render folder name to check")
    ap.add_argument("--out", required=True, help="report folder")
    ap.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    a = ap.parse_args()
    master, home, out = Path(a.master), Path(a.home), Path(a.out)

    man = json.loads((master / "manifest.json").read_text())
    roots = [os.path.expanduser(r) for r in man["src_roots"]]
    db = duckdb.connect(str(home / "library.duckdb"), read_only=True)
    lib = {r[0]: r for r in db.execute(
        "select id, path, duration_s, sample_rate, channels, bit_depth, file_format, file_size_bytes "
        "from samples").fetchall() if any(r[1].startswith(x.rstrip('/') + '/') for x in roots)}
    by_path = {r[1]: r for r in lib.values()}

    # picks: manifest src is relative to one of the src_roots
    picked: dict[str, list[str]] = collections.defaultdict(list)
    cats = []
    for cat, c in man["categories"].items():
        cats.append((cat, c.get("files", 0), c.get("families", 0), c.get("source_samples", 0)))
        for e in c.get("entries", []):
            for r in roots:
                p = os.path.join(r, e["src"])
                if p in by_path:
                    picked[p].append(f"{cat}/{e['out']}")
                    break

    reasons = why_reasons(home, master)
    dropped = []
    for sid, r in lib.items():
        if r[1] in picked:
            continue
        rs = reasons.get(sid) or [("", "not taken: no category recorded a reason (unrecognized or out-ranked)", "")]
        dropped.append((r[1], "; ".join(f"{c}:{why}" + (f" ({d})" if d not in (None, "") else "") for c, why, d in rs)))
    reason_counts = collections.Counter(
        why for _, s in dropped for why in {x.split(":", 1)[1].split(" (")[0] for x in s.split("; ")})

    # folders: master and every render
    folders = []
    for base in [master] + sorted(p for p in Path(a.renders).iterdir() if p.is_dir()):
        counts = collections.Counter(str(rel.parent) for _, rel in walk_render(base))
        for f, n in sorted(counts.items()):
            folders.append((base.name, f, n, "OVER" if n > FOLDER_LIMIT else ""))

    # Digitakt checks on the render
    dt_rows, dt_bytes = [], 0
    for p, rel in walk_render(Path(a.renders) / a.digitakt):
        i = sf.info(str(p))
        bits = {"PCM_16": 16, "PCM_24": 24, "PCM_32": 32, "FLOAT": 32}.get(i.subtype, 0)
        issues = []
        if i.samplerate != DT_RATE: issues.append(f"rate {i.samplerate}")
        if bits != DT_BITS: issues.append(f"subtype {i.subtype}")
        if i.channels > 2: issues.append(f"{i.channels} channels")
        if i.duration > DT_LONG_S: issues.append(f"long {i.duration:.0f}s")
        sz = p.stat().st_size
        dt_bytes += sz
        dt_rows.append((str(rel), i.samplerate, i.subtype, i.channels, round(i.duration, 3), sz, "; ".join(issues)))
    src_formats = collections.Counter(
        (r[6], r[3], r[5]) for r in lib.values())

    md = [f"# Build report: {master}", "",
          f"Library samples: {len(lib)}; in the master: {len(picked)}; left out: {len(dropped)}", "",
          "## Categories", "", "| Category | Files | Families | Source samples |", "|---|---:|---:|---:|"]
    md += [f"| {c} | {n} | {fa} | {s} |" for c, n, fa, s in cats]
    md += ["", "## Why files were left out (a file can have several reasons)", "", "| Reason | Files |", "|---|---:|"]
    md += [f"| {r} | {n} |" for r, n in reason_counts.most_common()]
    big = [f for f in folders if f[3]]
    md += ["", f"## Folders over {FOLDER_LIMIT} files", ""]
    md += [f"- {b}: `{f}`: {n}" for b, f, n, _ in big] or ["None."]
    md += ["", "## Largest folders per output", ""]
    for b in sorted({f[0] for f in folders}):
        top = max((f for f in folders if f[0] == b), key=lambda t: t[2])
        md.append(f"- {b}: {sum(f[2] for f in folders if f[0] == b)} files in "
                  f"{sum(1 for f in folders if f[0] == b)} folders; largest `{top[1]}` ({top[2]})")
    bad = [r for r in dt_rows if r[6]]
    md += ["", f"## Digitakt render `{a.digitakt}`", "",
           f"{len(dt_rows)} files, {dt_bytes / 1e6:.1f} MB "
           f"({dt_bytes / 1e6 / DT_PROJECT_MB:.0%} of one project's {DT_PROJECT_MB} MB sample RAM)", ""]
    md += [f"- `{r[0]}`: {r[6]}" for r in bad] or ["Every file is 48 kHz / 16-bit, mono or stereo, under 66 s."]
    md += ["", "## Source formats (format, sample rate, bit depth: files)", ""]
    md += [f"- {f} {sr} Hz {b}-bit: {n}" for (f, sr, b), n in src_formats.most_common()]
    text = "\n".join(md) + "\n"

    if a.dry_run:
        print(text)
        print(f"(dry run: would write {out}/summary.md, dropped.csv, folders.csv, digitakt-files.csv)")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(text)
    for name, head, rows in (("dropped.csv", ["source", "reasons"], sorted(dropped)),
                             ("folders.csv", ["output", "folder", "files", "over_limit"], folders),
                             ("digitakt-files.csv", ["path", "rate", "subtype", "channels", "seconds", "bytes", "issues"], dt_rows),
                             ("picked.csv", ["source", "master_paths"], sorted((k, " | ".join(v)) for k, v in picked.items()))):
        with open(out / name, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(head); w.writerows(rows)
    print(text)
    print(f"Wrote {out}/summary.md, dropped.csv, folders.csv, digitakt-files.csv, picked.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
