"""Run a strategy against the simulated expert and score it."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from prereq.data import Dataset
from prereq.oracle import Oracle
from prereq.strategies import STRATEGIES


@dataclass(frozen=True)
class Outcome:
    strategy: str
    questions: int
    accuracy: float          # over all ordered pairs, against the chosen truth
    precision: float         # of predicted prerequisites, share that are real
    recall: float            # of real prerequisites, share predicted
    params: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def score(pred: np.ndarray, truth: np.ndarray) -> tuple[float, float, float]:
    off = ~np.eye(truth.shape[0], dtype=bool)
    p, t = pred[off], truth[off]
    acc = float((p == t).mean())
    tp = int((p & t).sum())
    prec = tp / int(p.sum()) if p.sum() else 1.0
    rec = tp / int(t.sum()) if t.sum() else 1.0
    return acc, prec, rec


def run(
    ds: Dataset,
    strategy: str,
    seed: int = 0,
    transitive_truth: bool = True,
    **params,
) -> Outcome:
    """`transitive_truth=True` scores against the closure of the ground-truth DAG, which is
    what the implication-based heuristics reconstruct; False scores against direct edges only."""
    truth = ds.truth(transitive_truth)
    oracle = Oracle(truth)
    pred = STRATEGIES[strategy](ds, oracle, rng=np.random.default_rng(seed), **params)
    acc, prec, rec = score(pred, truth)
    return Outcome(strategy, oracle.questions, acc, prec, rec,
                   ",".join(f"{k}={v}" for k, v in params.items()))


def repeat(ds: Dataset, strategy: str, seeds: int = 100, **kw) -> tuple[float, float, float]:
    """Mean questions, std questions, mean accuracy over `seeds` random seeds."""
    outs = [run(ds, strategy, seed=s, **kw) for s in range(seeds)]
    q = np.array([o.questions for o in outs], dtype=float)
    a = np.array([o.accuracy for o in outs])
    return float(q.mean()), float(q.std()), float(a.mean())
