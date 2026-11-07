#!/usr/bin/env python3
"""Folder structure of a render (or the master): per category, its subfolders, how many files
each holds, which are numbered overflow ("kick-2": split by a files-per-folder cap rather than
by sound) and which are over a limit. For reviewing how browsable a build is.

Reads only the folder tree. Writes structure.md and structure.csv into --out (nothing with
--dry-run).

  python -I scripts/folder_structure.py --root out/renders/digitakt_2_50 --out reports/phase2 [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import sys
from pathlib import Path

AUDIO = (".wav", ".aif", ".aiff", ".flac")
# a numbered sibling a files-per-folder cap made: "<name>-2", "<name>-3" (a render's split)
OVERFLOW_RE = re.compile(r"-(\d+)$")


def tree(root: Path) -> dict[str, dict[str, int]]:
    """{category folder: {subfolder (relative, "" for files directly in it): audio files}}."""
    out: dict[str, dict[str, int]] = collections.defaultdict(dict)
    for dp, _, fs in os.walk(root):
        n = sum(1 for f in fs if f.lower().endswith(AUDIO))
        if not n:
            continue
        rel = Path(dp).relative_to(root).parts
        if not rel:
            out["(root)"][""] = n
            continue
        out[rel[0]]["/".join(rel[1:])] = n
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="a render or master folder")
    ap.add_argument("--limit", type=int, default=50, help="files per folder to flag (default 50)")
    ap.add_argument("--out", required=True, help="report folder")
    ap.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    a = ap.parse_args()
    root = Path(a.root)
    t = tree(root)

    rows, md = [], [f"# Folder structure: `{root}`", "",
                    "| Category | Files | Groups | Subfolders | Largest | Median | Overflow (`-2`...) | Over limit |",
                    "|---|---:|---:|---:|---:|---:|---:|---:|"]
    total_files = total_folders = 0
    for cat in sorted(t):
        subs = t[cat]
        counts = sorted(subs.values())
        over = [s for s, n in subs.items() if n > a.limit]
        ovf = [s for s in subs if OVERFLOW_RE.search(s.rsplit("/", 1)[-1])]
        # a three-level render: the group folders between the category and its families
        groups = {s.split("/", 1)[0] for s in subs if "/" in s}
        total_files += sum(counts)
        total_folders += len(subs)
        md.append(f"| {cat} | {sum(counts)} | {len(groups) or '-'} | {len(subs)} | {counts[-1]} "
                  f"| {counts[len(counts) // 2]} | {len(ovf)} | {len(over)} |")
        for s, n in sorted(subs.items()):
            rows.append((cat, s or "(files directly in the category)", n,
                         "overflow" if s in ovf else "", "over" if n > a.limit else ""))
    md += ["", f"{total_files} files in {total_folders} folders.", "", "## Subfolders", ""]
    for cat in sorted(t):
        md.append(f"- **{cat}**: " + ", ".join(f"`{s or '.'}` ({n})" for s, n in sorted(t[cat].items())))
    text = "\n".join(md) + "\n"

    print(text)
    if a.dry_run:
        print(f"(dry run: would write {a.out}/structure.md and structure.csv)")
        return 0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "structure.md").write_text(text)
    with open(out / "structure.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "subfolder", "files", "overflow", "over_limit"])
        w.writerows(rows)
    print(f"Wrote {out}/structure.md, structure.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
