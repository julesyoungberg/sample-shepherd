"""Run systems over a label set and print the results as plain-text tables."""
from __future__ import annotations

import collections
import json
import random
from pathlib import Path
from typing import Sequence

from sample_shepherd.evaluate import CATEGORIES
from sample_shepherd.evaluate.baselines import BASELINES
from sample_shepherd.evaluate.labels import Label, path_key
from sample_shepherd.evaluate.metrics import NONE, Result, evaluate
from sample_shepherd.evaluate.predictions import align, load_predictions


def run(labels: list[Label], baselines: Sequence[str] = tuple(BASELINES),
        predictions: Sequence[Path] = (), ci_rounds: int = 1000) -> list[Result]:
    """Every chosen baseline, then every predictions file, scored on `labels`."""
    paths, truth = [lab.path for lab in labels], [lab.category for lab in labels]
    results = []
    for b in baselines:
        if b not in BASELINES:
            raise ValueError(f"unknown baseline {b!r} (one of {', '.join(BASELINES)})")
        fn = BASELINES[b]
        results.append(evaluate(b, paths, truth, [fn(p, labels) for p in paths], ci_rounds))
    for f in predictions:
        name = f.parent.name if f.name == "manifest.json" else f.stem
        results.append(evaluate(name, paths, truth, align(labels, load_predictions(f)), ci_rounds))
    return results


def by_provenance(labels: list[Label], results: list[Result]) -> dict[str, dict[str, tuple[int, int]]]:
    """{system: {provenance: (correct, n)}}."""
    wrong = {r.system: collections.Counter(p for p, _, _ in r.errors) for r in results}
    out = {}
    for r in results:
        cells: dict[str, list[int]] = {}
        misses = wrong[r.system].copy()
        for lab in labels:
            c = cells.setdefault(lab.provenance or "(none)", [0, 0])
            c[1] += 1
            if misses[lab.path]:
                misses[lab.path] -= 1
            else:
                c[0] += 1
        out[r.system] = {k: (v[0], v[1]) for k, v in sorted(cells.items())}
    return out


def _f(x: float | None, pct: bool = False) -> str:
    if x is None:
        return "-"
    return f"{x:.0%}" if pct else f"{x:.2f}"


def format_report(labels: list[Label], results: list[Result], detail: str | None = None,
                  show_errors: int = 20) -> str:
    lines = []
    prov = collections.Counter(lab.provenance or "(none)" for lab in labels)
    cats = collections.Counter(lab.category for lab in labels)
    lines.append(f"labels: {len(labels)} ({', '.join(f'{k} {v}' for k, v in sorted(prov.items()))}); "
                 f"{len(cats)} of {len(CATEGORIES)} categories")
    lines.append("")
    w = max([len(r.system) for r in results] + [6])
    lines.append(f"{'system':<{w}}  {'accuracy (95% CI)':<18}  {'coverage':>8}  {'acc|decided':>11}  {'macro-F1':>8}")
    for r in results:
        lines.append(f"{r.system:<{w}}  {r.accuracy:.2f} ({r.ci[0]:.2f}-{r.ci[1]:.2f})    "
                     f"{_f(r.coverage, True):>8}  {_f(r.accuracy_decided):>11}  {r.macro_f1:>8.2f}")

    bp = by_provenance(labels, results)
    provs = sorted(prov)
    if len(provs) > 1:
        lines += ["", "accuracy by label provenance (correct/n)"]
        cw = max(len(p) for p in provs) + 2
        lines.append(f"{'system':<{w}}" + "".join(f"{p:>{cw}}" for p in provs))
        for r in results:
            lines.append(f"{r.system:<{w}}" + "".join(
                f"{'%d/%d' % bp[r.system][p]:>{cw}}" for p in provs))

    shown = [r for r in results if r.system == detail] if detail else results[-1:]
    if detail and not shown:
        raise ValueError(f"no system called {detail!r} (have: {', '.join(r.system for r in results)})")
    for r in shown:
        lines += ["", f"per category: {r.system}",
                  f"{'category':<10} {'support':>7} {'predicted':>9} {'precision':>9} {'recall':>7} {'f1':>5}"]
        for c, s in r.per_class.items():
            lines.append(f"{c:<10} {s.support:>7} {s.predicted:>9} {_f(s.precision):>9} "
                         f"{_f(s.recall):>7} {_f(s.f1):>5}")
        lines += ["", f"confusion: {r.system} (rows: truth; columns: predicted, first 5 letters)"]
        cols = [c for c in CATEGORIES if any(c in row for row in r.confusion.values())]
        if any(NONE in row for row in r.confusion.values()):
            cols.append(NONE)
        lines.append(f"{'':<10}" + "".join(f"{c[:5] if c != NONE else 'none':>6}" for c in cols))
        for t in [c for c in CATEGORIES if c in r.confusion]:
            row = r.confusion[t]
            lines.append(f"{t:<10}" + "".join(f"{row.get(c, 0) or '.':>6}" for c in cols))
        if show_errors and r.errors:
            lines += ["", f"errors: {r.system} ({len(r.errors)}; first {min(show_errors, len(r.errors))})"]
            for p, t, x in r.errors[:show_errors]:
                lines.append(f"  {t:>9} <- {x:<9} {p}")
    return "\n".join(lines)


def results_json(labels: list[Label], results: list[Result]) -> str:
    bp = by_provenance(labels, results)
    return json.dumps({
        "labels": len(labels),
        "results": [dict(r.to_dict(), by_provenance={k: {"correct": c, "n": n} for k, (c, n) in bp[r.system].items()})
                    for r in results],
    }, indent=1)


def sample_sheet(manifest: Path, per_category: int, seed: int,
                 exclude: Sequence[Label] = ()) -> list[dict[str, str]]:
    """A labeling sheet: up to `per_category` placed samples from each category of a master,
    drawn at random (seeded), minus paths already labeled. The category column is left blank
    on purpose, so whoever listens isn't anchored by what Fourier decided."""
    man = json.loads((manifest / "manifest.json" if manifest.is_dir() else manifest).read_text(encoding="utf-8"))
    done = {lab.key for lab in exclude}
    rng = random.Random(seed)
    rows = []
    for cat in sorted(man.get("categories", {})):
        srcs = sorted({e["src"] for e in man["categories"][cat].get("entries", []) or []
                       if e.get("src") and path_key(e["src"]) not in done})
        for src in rng.sample(srcs, min(per_category, len(srcs))):
            rows.append({"path": src, "category": "", "provenance": "listened", "note": ""})
    rng.shuffle(rows)                      # mixed order, so the sheet doesn't give categories away
    return rows
