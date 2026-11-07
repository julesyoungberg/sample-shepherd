#!/usr/bin/env python3
"""Write a Fourier ratings CSV that files samples by their folder name, for packs whose file
names mislead Fourier's drum rules (Brad Brunazzi's "SD_" prefix reads as "snare drum").

For every library sample whose path matches --pack and whose name matches --name, the nearest
folder that names exactly one category decides it; failing that, the file name with --name's
match cut off, when it names exactly one. Only misrouted samples get a `misfiled` row: one the
last build put in another category, or one placed nowhere with no reason in Fourier's why log
(recognized, yet no category took it). A sample left out for its budget, the vendor cap,
clipping and the like is left alone, so a rating never forces a pick. Import the CSV with
`fourier review import <csv>` (`fourier review rate <path> clear` undoes one).

Reads Fourier's database (read-only) and the master's manifest. Writes only --out, and
nothing with --dry-run.

  . ~/sample-work/fourier.env
  python -I scripts/folder_ratings.py --pack "Brad Brunazzi Vintage Drum Machines" \
      --name '^SD_' --out config/ratings/brad-brunazzi-sd.csv [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

import duckdb

W = Path.home() / "sample-work"
# the folder a file sits in -> its category (first match wins, nearest folder first)
FOLDER_CATS = [
    (r"(?<![a-z])kicks?(?![a-z])", "KICKS"),
    (r"(?<![a-z])snares?(?![a-z])", "SNARES"),
    (r"(?<![a-z])claps?(?![a-z])", "CLAPS"),
    (r"hi ?-?hats?|(?<![a-z])hats?(?![a-z])", "HATS"),
    (r"(?<![a-z])toms?(?![a-z])", "TOMS"),
    (r"cymbals?|(?<![a-z])(?:crash|ride)(?![a-z])", "CYMBALS"),
    (r"(?<![a-z])percs?(?:ussion)?(?![a-z])", "PERC"),
]
SKIP_FOLDERS = re.compile(r"^(?:wet|dry|one ?shots?|custom one shots)$", re.I)


def named(text: str) -> set[str]:
    text = text.replace("_", " ")
    return {cat for rx, cat in FOLDER_CATS if re.search(rx, text, re.I)}


def category_of(rel: str, cut: str) -> tuple[str | None, str]:
    """(category, what decided it); None when the folder or name is ambiguous or silent."""
    for part in reversed(Path(rel).parent.parts):
        if SKIP_FOLDERS.match(part):
            continue
        cats = named(part)
        if len(cats) == 1:
            return cats.pop(), "folder"
        if cats:
            return None, f"folder names {len(cats)} kinds"
        break                              # nearest real folder names nothing: ask the name
    cats = named(re.sub(cut, "", os.path.splitext(os.path.basename(rel))[0]))
    return (cats.pop(), "name") if len(cats) == 1 else (None, "name names none or several")


def why_out_ids(home: Path, master: Path) -> set[int]:
    """Sample ids some category's why log gives a reason for leaving out."""
    sys.path.insert(0, str(W / "vendor/fourier-samples/src"))
    from fourier.packs import why_log
    ids = set()
    for f in (home / "why" / why_log.master_key(master)).glob("*.json"):
        for reasons in (json.loads(f.read_text()).get("out") or {}).values():
            ids |= {int(i) for i in reasons}
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True, help="a piece of the library path that names the pack")
    ap.add_argument("--name", default=".", help="regex on the file name (default: every file)")
    ap.add_argument("--master", default=str(W / "out/master"))
    ap.add_argument("--home", default=os.environ.get("FOURIER_HOME", str(W / "fourier-home")))
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the rows, write nothing")
    a = ap.parse_args()

    man = json.loads((Path(a.master) / "manifest.json").read_text())
    roots = [os.path.expanduser(r) for r in man["src_roots"]]
    placed = {}
    for cat, c in man["categories"].items():
        for e in c.get("entries", []):
            for r in roots:
                placed.setdefault(os.path.join(r, e["src"]), cat)

    explained = why_out_ids(Path(a.home), Path(a.master))
    db = duckdb.connect(str(Path(a.home) / "library.duckdb"), read_only=True)
    rows, ok, left_out, unknown = [], 0, 0, []
    for sid, path in db.execute("select id, path from samples where path like ? order by path",
                                [f"%/{a.pack}/%"]).fetchall():
        if not re.search(a.name, os.path.basename(path)):
            continue
        rel = path.split(f"/{a.pack}/", 1)[1]
        cat, by = category_of(rel, a.name)
        now = placed.get(path)
        if cat is None:
            unknown.append(f"{rel}  ({by})")
        elif now == cat:
            ok += 1
        elif now is None and sid in explained:
            left_out += 1                  # a gate or the budget left it out: not a routing fault
        else:
            rows.append((path, "misfiled", cat, "file", now or "(nowhere)", f"{rel}  (by {by})"))

    for path, _, cat, _, now, rel in rows:
        print(f"{now:>10} -> {cat:<8} {rel}")
    print(f"\n{len(rows)} misrouted, to rate misfiled; {ok} already in the right category; "
          f"{left_out} left out by a gate or budget (left alone); {len(unknown)} ambiguous (left alone)")
    for rel in unknown:
        print(f"  ambiguous: {rel}")
    if a.dry_run:
        print(f"(dry run: would write {a.out})")
        return 0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "rating", "category", "scope"])
        w.writerows(r[:4] for r in rows)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
