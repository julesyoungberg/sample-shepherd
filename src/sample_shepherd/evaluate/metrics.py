"""Classification metrics for category routing, in plain Python (no numpy needed).

`None` as a prediction means the system abstained. It counts as wrong for accuracy and recall
but isn't a false positive for any category; `coverage` reports how often a system decided.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

NONE = "(none)"


@dataclass
class ClassStats:
    support: int = 0          # labels in this category
    predicted: int = 0        # predictions of this category
    correct: int = 0

    @property
    def precision(self) -> float | None:
        return self.correct / self.predicted if self.predicted else None

    @property
    def recall(self) -> float | None:
        return self.correct / self.support if self.support else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision or 0.0, self.recall or 0.0
        if not self.support and not self.predicted:
            return None
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass
class Result:
    system: str
    n: int
    correct: int
    decided: int
    per_class: dict[str, ClassStats]
    confusion: dict[str, dict[str, int]]          # truth -> predicted (or NONE) -> count
    ci: tuple[float, float] = (0.0, 0.0)
    errors: list[tuple[str, str, str]] = field(default_factory=list)   # (path, truth, predicted)

    @property
    def accuracy(self) -> float:
        return self.correct / self.n if self.n else 0.0

    @property
    def coverage(self) -> float:
        return self.decided / self.n if self.n else 0.0

    @property
    def accuracy_decided(self) -> float | None:
        return self.correct / self.decided if self.decided else None

    @property
    def macro_f1(self) -> float:
        """Mean F1 over the categories that have labels (a category nobody labeled can't be
        scored fairly, so it's left out)."""
        fs = [s.f1 or 0.0 for s in self.per_class.values() if s.support]
        return sum(fs) / len(fs) if fs else 0.0

    def to_dict(self) -> dict:
        return {
            "system": self.system, "n": self.n, "accuracy": self.accuracy,
            "accuracy_ci95": list(self.ci), "coverage": self.coverage,
            "accuracy_when_decided": self.accuracy_decided, "macro_f1": self.macro_f1,
            "per_category": {c: {"support": s.support, "predicted": s.predicted,
                                 "precision": s.precision, "recall": s.recall, "f1": s.f1}
                             for c, s in self.per_class.items()},
            "confusion": self.confusion,
            "errors": [{"path": p, "truth": t, "predicted": x} for p, t, x in self.errors],
        }


def bootstrap_ci(hits: list[bool], rounds: int = 1000, seed: int = 0) -> tuple[float, float]:
    """95% percentile interval for accuracy. With a few dozen labels it's wide; that's the point."""
    if not hits:
        return (0.0, 0.0)
    rng, n = random.Random(seed), len(hits)
    accs = sorted(sum(hits[rng.randrange(n)] for _ in range(n)) / n for _ in range(rounds))
    return (accs[int(0.025 * rounds)], accs[min(rounds - 1, int(0.975 * rounds))])


def evaluate(system: str, paths: list[str], truth: list[str], predicted: list[str | None],
             ci_rounds: int = 1000) -> Result:
    if not (len(paths) == len(truth) == len(predicted)):
        raise ValueError("paths, truth and predictions differ in length")
    per: dict[str, ClassStats] = {}
    conf: dict[str, dict[str, int]] = {}
    hits, errors = [], []
    for p, t, x in zip(paths, truth, predicted):
        per.setdefault(t, ClassStats()).support += 1
        if x is not None:
            per.setdefault(x, ClassStats()).predicted += 1
        ok = x == t
        if ok:
            per[t].correct += 1
        else:
            errors.append((p, t, x or NONE))
        row = conf.setdefault(t, {})
        row[x or NONE] = row.get(x or NONE, 0) + 1
        hits.append(ok)
    return Result(system, len(truth), sum(hits), sum(x is not None for x in predicted),
                  dict(sorted(per.items())), conf, bootstrap_ci(hits, ci_rounds), errors)
