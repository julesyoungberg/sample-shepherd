"""A real system's category decisions, read from its output files.

- A Fourier master's `manifest.json`: `{"src_roots": [...], "categories": {CAT: {"entries":
  [{"src": <path relative to a src root>, "out": ...}]}}}`. A sample that isn't in the master
  is "not placed", which may be a routing miss or just the budget, so it counts as abstaining.
- A CSV with `path` and `category` columns (any other system, e.g. an export from a model).
  An empty category is an abstention.

Paths are matched to labels by tail (`path_key`): a prediction for
"/Users/x/packs/2024/Acme/Kicks/K1.wav" answers a label for "Acme/Kicks/K1.wav".
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from sample_shepherd.evaluate.labels import Label, path_key

Predictions = dict[str, "str | None"]          # path_key -> category (None: abstained)


def load_predictions(path: Path) -> Predictions:
    if path.is_dir():
        path = path / "manifest.json"
    if path.suffix.lower() == ".json":
        man = json.loads(path.read_text(encoding="utf-8"))
        if "categories" not in man:
            raise ValueError(f"{path}: not a Fourier master manifest (no 'categories')")
        out: Predictions = {}
        for cat, c in man["categories"].items():
            for e in c.get("entries", []) or []:
                if e.get("src"):
                    out.setdefault(path_key(e["src"]), cat.upper())
        return out
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = csv.DictReader(fh)
        if not {"path", "category"} <= set(rows.fieldnames or []):
            raise ValueError(f"{path}: needs path and category columns")
        for r in rows:
            if (r.get("path") or "").strip():
                out[path_key(r["path"])] = (r.get("category") or "").strip().upper() or None
    return out


def align(labels: list[Label], preds: Predictions) -> list[str | None]:
    """The prediction for each label, matching by path tail; None when there's none."""
    by_tail: dict[str, list[str]] = {}
    for k in preds:
        by_tail.setdefault(k.rsplit("/", 1)[-1], []).append(k)
    out = []
    for lab in labels:
        k = lab.key
        if k in preds:
            out.append(preds[k])
            continue
        hits = [p for p in by_tail.get(k.rsplit("/", 1)[-1], []) if p.endswith("/" + k) or k.endswith("/" + p)]
        cats = {preds[p] for p in hits}
        out.append(cats.pop() if len(cats) == 1 else None)
    return out
