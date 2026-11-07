#!/usr/bin/env python3
"""Phase 3 project coverage: for each Digitakt II project, which of its samples the new library
already holds (the same source file, by drive_match), so you can see what a project still
needs from the old +Drive files before anything is removed.

Per project: samples used, matched to a source, in the new library (with the new +Drive path),
and the ones that are only on the old +Drive. Read-only; it changes no project and no file.

  . ~/sample-work/fourier.env
  python -I scripts/project_coverage.py --drive device/drive-listing.csv --projects device/projects \
      --out reports/phase3 [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_match as dm  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive", required=True, help="+Drive listing: CSV (path[,size][,seconds]), text, or a folder copy")
    ap.add_argument("--projects", required=True, help="folder of per-project sample lists (<project>.txt)")
    ap.add_argument("--master", default=str(dm.W / "out/full/master"))
    ap.add_argument("--render", default=str(dm.W / "out/full/renders/digitakt_2_50"))
    ap.add_argument("--home", default=os.environ.get("FOURIER_HOME", str(dm.W / "fourier-home")))
    ap.add_argument("--out", required=True, help="report folder")
    ap.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    a = ap.parse_args()

    drive, projects = Path(a.drive), Path(a.projects)
    if not drive.exists() or not projects.is_dir() or not any(projects.glob("*.txt")):
        print("Missing input: this needs the +Drive listing and the per-project sample lists from "
              "device session 1. Nothing guessed, nothing written.", file=sys.stderr)
        return 2
    master = Path(a.master)
    roots = [os.path.expanduser(r) for r in json.loads((master / "manifest.json").read_text())["src_roots"]]
    matcher = dm.Matcher(dm.load_sources(Path(a.home) / "library.duckdb", roots))
    new = dm.new_paths(master, Path(a.render))
    listing = {dm.norm_drive(f.path): f for f in dm.load_drive(drive)}

    rows, md = [], ["# Project coverage", "",
                    "| Project | Samples | Matched to a source | In the new library | Only on the old +Drive |",
                    "|---|---:|---:|---:|---:|"]
    for proj, paths in dm.read_projects(projects).items():
        n = matched = covered = 0
        for p in sorted(paths):
            n += 1
            f = listing.get(dm.norm_drive(p)) or dm.DriveFile(p)
            m = matcher.match(f)
            src = m.source.path if m.source else ""
            newp = new.get(src, "")
            matched += bool(src)
            covered += bool(newp)
            rows.append((proj, p, src, newp, m.how, "yes" if newp else "no"))
        md.append(f"| {proj} | {n} | {matched} | {covered} | {n - covered} |")
    text = "\n".join(md) + "\n"
    print(text)
    if a.dry_run:
        print(f"(dry run: would write {a.out}/project-coverage.md and project-coverage.csv)")
        return 0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "project-coverage.md").write_text(text)
    with open(out / "project-coverage.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["project", "+Drive path", "source path", "new path", "matched by", "in new library"])
        w.writerows(rows)
    print(f"Wrote {out}/project-coverage.md, project-coverage.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
