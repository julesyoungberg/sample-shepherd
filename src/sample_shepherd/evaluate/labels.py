"""Ground-truth labels: which category a library sample belongs in.

A label file is a CSV with columns `path,category,provenance,note`:

- path: the sample's path relative to the library root (e.g. "2024/Acme Drums/Kicks/Kick 01.wav"),
  or a shorter tail of it ("Kicks/Kick 01.wav") when the full path isn't known. Matching is by
  path tail, case and audio extension aside (see `path_key`).
- category: one of `CATEGORIES`.
- provenance: where the label came from, so results can be read per source. The ones in use:
  `listened` (a person auditioned it), `rated-keep` / `rated-misfiled` (imported from Fourier
  ratings), `folder-rule` (the pack's own folder decided it, e.g. scripts/folder_ratings.py),
  `documented` (a case a phase report settles), `synthetic` (an invented name that pins down a
  naming pattern; says nothing about the real library's accuracy).
- note: free text.
"""
from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from sample_shepherd.evaluate import CATEGORIES

AUDIO_EXT = re.compile(r"\.(wav|wave|aif|aiff|flac|mp3|ogg)$", re.I)
FIELDS = ["path", "category", "provenance", "note"]


@dataclass(frozen=True)
class Label:
    path: str
    category: str
    provenance: str = ""
    note: str = ""

    @property
    def key(self) -> str:
        return path_key(self.path)


def path_key(path: str) -> str:
    """A path as labels and predictions are matched: forward slashes, no leading slash, no audio
    extension, lowercase."""
    p = path.replace("\\", "/").strip().lstrip("/")
    return AUDIO_EXT.sub("", p).lower()


def bundled_labels() -> Path:
    """The seed label set: bundled in the wheel, or eval/labels/ in a checkout."""
    pkg = Path(__file__).resolve().parent.parent / "eval-labels" / "categories.csv"
    if pkg.exists():
        return pkg
    return Path(__file__).resolve().parents[3] / "eval" / "labels" / "categories.csv"


def load_labels(path: Path) -> list[Label]:
    """Read and check a label file: known categories, no path labeled twice."""
    out, seen = [], {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = csv.DictReader(fh)
        missing = {"path", "category"} - set(rows.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: no {', '.join(sorted(missing))} column")
        for n, r in enumerate(rows, start=2):
            p, cat = (r.get("path") or "").strip(), (r.get("category") or "").strip().upper()
            if not p or not cat:
                continue                   # a labeling sheet's row nobody has filled in yet
            if cat not in CATEGORIES:
                raise ValueError(f"{path}:{n}: unknown category {cat!r} (one of {', '.join(CATEGORIES)})")
            lab = Label(p, cat, (r.get("provenance") or "").strip(), (r.get("note") or "").strip())
            if lab.key in seen:
                raise ValueError(f"{path}:{n}: {p!r} is already labeled on line {seen[lab.key]}")
            seen[lab.key] = n
            out.append(lab)
    return out


def write_labels(path: Path, labels: list[Label]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for lab in labels:
            w.writerow({"path": lab.path, "category": lab.category,
                        "provenance": lab.provenance, "note": lab.note})


def relative_to_root(path: str, root: str | None) -> str | None:
    """`path` relative to the library root; None when it's absolute and not under the root."""
    p = path.replace("\\", "/")
    if root:
        r = os.path.expanduser(root).replace("\\", "/").rstrip("/") + "/"
        if p.startswith(r):
            return p[len(r):]
    return None if p.startswith("/") or re.match(r"^[A-Za-z]:/", p) else p


def labels_from_ratings(path: Path, root: str | None) -> tuple[list[Label], list[str]]:
    """Labels from human ratings: a Fourier ratings store (ratings.json) or a review CSV
    (`path,rating,category`, as `fourier review import` reads).

    In ratings.json a Keep confirms the category it was rated in (`category`), and a Misfiled
    names where it belongs in `target` (its `category` is where it was, i.e. wrong). In a
    review CSV, `category` on a misfiled row is where it belongs. A Drop says nothing about the
    category, so it's skipped. Returns (labels, reasons rows were skipped)."""
    entries: list[tuple[str, str, str]] = []           # (path, verdict, category it belongs in)
    if path.suffix.lower() == ".json":
        store = json.loads(path.read_text(encoding="utf-8"))
        for p, r in (store.get("ratings") or {}).items():
            v = (r.get("verdict") or "").lower()
            cat = r.get("category") if v == "keep" else r.get("target") if v == "misfiled" else None
            entries.append((p, v, cat or ""))
    else:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                v = (r.get("rating") or r.get("verdict") or "").strip().lower()
                entries.append(((r.get("path") or "").strip(), v, (r.get("category") or "").strip()))

    labels, skipped = [], []
    for p, v, cat in entries:
        cat = cat.upper()
        if v not in ("keep", "misfiled"):
            skipped.append(f"{p}: {v or 'no'} verdict says nothing about the category")
            continue
        if cat not in CATEGORIES:
            skipped.append(f"{p}: {v} with no known category ({cat or 'none'})")
            continue
        rel = relative_to_root(p, root)
        if rel is None:
            skipped.append(f"{p}: not under the library root {root or '(none given: pass --root)'}")
            continue
        labels.append(Label(rel, cat, f"rated-{v}", f"imported from {path.name}"))
    return labels, skipped


HUMAN = ("listened", "rated-keep", "rated-misfiled")


def merge(existing: list[Label], new: list[Label]) -> tuple[list[Label], int, int, int]:
    """Add new labels. A path already labeled keeps its label unless the new one is a human
    label (listened / rated-*) and the old one isn't: then the human one replaces it, whether it
    changes the category ("changed") or agrees ("confirmed"), so `--provenance listened ...`
    picks it up. Returns (labels, added, changed, confirmed)."""
    by_key = {lab.key: i for i, lab in enumerate(existing)}
    out, added, changed, confirmed = list(existing), 0, 0, 0
    for lab in new:
        i = by_key.get(lab.key)
        if i is None:
            by_key[lab.key] = len(out)
            out.append(lab)
            added += 1
        elif lab.provenance in HUMAN and out[i].provenance not in HUMAN:
            if out[i].category != lab.category:
                changed += 1
            else:
                confirmed += 1
            out[i] = lab
        elif lab.provenance in HUMAN and out[i].category != lab.category:
            out[i] = lab                   # a newer human rating wins over an older one
            changed += 1
    return out, added, changed, confirmed
