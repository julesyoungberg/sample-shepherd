#!/usr/bin/env python3
"""Phase 3 delete list: every +Drive sample, whether it came from the source library and
already has an equivalent in the new library, and whether any project uses it.

Status (the deletion policy):
- SAFE: matched to a source file (drive_match: hash, or name + converted size, or name +
  duration), that source is in the new library, and no project uses this +Drive file;
- KEEP-USED: matched and in the new library, but a project uses it;
- KEEP-UNMATCHED: no single source matched, or the source isn't in the new library, or the
  file isn't from the source library at all. Never a candidate.
This only lists. It deletes nothing; you delete by hand, after checking.

Run it only with a real +Drive listing and the projects' sample lists from device session 1;
without them it stops.

  . ~/sample-work/fourier.env
  python -I scripts/delete_list.py --drive device/drive-listing.csv --projects device/projects \
      --out reports/phase3/delete-list.csv [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drive_match as dm  # noqa: E402

COLUMNS = ["+Drive path", "source path", "new path", "hash match (Y/N)", "used by projects", "status",
           "matched by"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drive", required=True, help="+Drive listing: CSV (path[,size][,seconds]), text, or a folder copy")
    ap.add_argument("--projects", required=True, help="folder of per-project sample lists (<project>.txt)")
    ap.add_argument("--master", default=str(dm.W / "out/full/master"))
    ap.add_argument("--render", default=str(dm.W / "out/full/renders/digitakt_2_50"))
    ap.add_argument("--home", default=os.environ.get("FOURIER_HOME", str(dm.W / "fourier-home")))
    ap.add_argument("--out", required=True, help="CSV to write")
    ap.add_argument("--dry-run", action="store_true", help="print the counts, write nothing")
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
    used: dict[str, list[str]] = collections.defaultdict(list)
    for proj, paths in dm.read_projects(projects).items():
        for p in paths:
            used[dm.norm_drive(p)].append(proj)

    rows, counts = [], collections.Counter()
    for f in dm.load_drive(drive):
        m = matcher.match(f)
        src = m.source.path if m.source else ""
        newp = new.get(src, "") if src else ""
        users = sorted(set(used.get(dm.norm_drive(f.path), [])))
        if not src or not newp:
            status = "KEEP-UNMATCHED"
        elif users:
            status = "KEEP-USED"
        else:
            status = "SAFE"
        counts[status] += 1
        how = m.how + (f" ({len(m.candidates)} candidates)" if m.how == "ambiguous" else "")
        if src and not newp:
            how += "; source not in the new library"
        rows.append((f.path, src, newp, "Y" if m.how == "hash" else "N", "; ".join(users) or "none", status, how))

    unused_projects = sorted(set(dm.norm_drive(p) for p in used) - {dm.norm_drive(f[0]) for f in rows})
    print(f"{len(rows)} +Drive samples: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if unused_projects:
        print(f"note: {len(unused_projects)} paths in the project lists aren't in the +Drive listing "
              f"(a listing that is incomplete, or a path written differently), e.g. {unused_projects[0]}")
    if a.dry_run:
        print(f"(dry run: would write {a.out})")
        return 0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows(sorted(rows, key=lambda r: (r[5] != "SAFE", r[0])))
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
