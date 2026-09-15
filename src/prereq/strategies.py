"""Query strategies. Each takes a dataset and an oracle and returns an (n, n) boolean matrix of
predicted prerequisite relationships. The oracle counts the questions.

* brute_force           ask every ordered pair
* heuristic_random      random pairs; skip pairs already implied; A->B settles B->A
* heuristic_by_topic    same, but exhaust one random topic's pairs before moving on
* heuristic_ordered     same, topics taken from most advanced to most basic (weighted in-degree)
* threshold             weights above `upper` are accepted, below `lower` rejected, the rest asked
* binary_search         rank positive-weight pairs; binary-search the cut-off with 3-vote probes

The three heuristics maintain a growing DAG of known prerequisites and treat any pair that is
already reachable in it as answered ("implied"), which is where their savings come from.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from prereq.data import Dataset
from prereq.oracle import Oracle

Strategy = Callable[..., np.ndarray]


def _reachable(known: np.ndarray, i: int, j: int) -> bool:
    """Is there a path i -> ... -> j in `known`? (small n; a BFS is plenty)"""
    n = known.shape[0]
    seen = np.zeros(n, dtype=bool)
    stack = [i]
    while stack:
        u = stack.pop()
        if u == j:
            return True
        if seen[u]:
            continue
        seen[u] = True
        stack.extend(np.flatnonzero(known[u]).tolist())
    return False


def _close(known: np.ndarray) -> np.ndarray:
    """Transitive closure: everything the asked answers imply."""
    r = known.copy()
    for k in range(r.shape[0]):
        r |= r[:, [k]] & r[[k], :]
    return r


def brute_force(ds: Dataset, oracle: Oracle, **_) -> np.ndarray:
    pred = np.zeros((ds.n, ds.n), dtype=bool)
    for i, j in ds.ordered_pairs():
        pred[i, j] = oracle.ask(i, j)
    return pred


def _settle_pair(ds: Dataset, oracle: Oracle, known: np.ndarray, i: int, j: int) -> None:
    """Resolve the unordered pair {i, j} into `known` with at most two questions."""
    if _reachable(known, i, j) or _reachable(known, j, i):
        return                                   # implied by what we already know
    if oracle.ask(i, j):
        known[i, j] = True
    elif oracle.ask(j, i):
        known[j, i] = True


def heuristic_random(ds: Dataset, oracle: Oracle, rng: np.random.Generator, **_) -> np.ndarray:
    known = np.zeros((ds.n, ds.n), dtype=bool)
    pairs = [(i, j) for i in range(ds.n) for j in range(i + 1, ds.n)]
    for k in rng.permutation(len(pairs)):
        i, j = pairs[k]
        _settle_pair(ds, oracle, known, i, j)
    return _close(known)


def _by_topic(ds: Dataset, oracle: Oracle, order: list[int]) -> np.ndarray:
    known = np.zeros((ds.n, ds.n), dtype=bool)
    done: set[int] = set()
    for t in order:
        for other in range(ds.n):
            if other == t or other in done:
                continue
            _settle_pair(ds, oracle, known, t, other)
        done.add(t)
    return _close(known)


def heuristic_by_topic(ds: Dataset, oracle: Oracle, rng: np.random.Generator, **_) -> np.ndarray:
    return _by_topic(ds, oracle, rng.permutation(ds.n).tolist())


def heuristic_ordered(ds: Dataset, oracle: Oracle, **_) -> np.ndarray:
    return _by_topic(ds, oracle, ds.advanced_to_basic())


def threshold(ds: Dataset, oracle: Oracle, lower: float, upper: float, **_) -> np.ndarray:
    """Accept weights > upper, reject weights < lower, ask about the band in between.
    Non-positive weights are rejected without asking (the reverse direction carries them)."""
    pred = np.zeros((ds.n, ds.n), dtype=bool)
    for i, j in ds.positive_pairs():
        w = ds.weights[i, j]
        if w > upper:
            pred[i, j] = True
        elif w >= lower:
            pred[i, j] = oracle.ask(i, j)
    return pred


def binary_search(ds: Dataset, oracle: Oracle, max_steps: int = 20, **_) -> np.ndarray:
    """Sort positive-weight pairs by weight. Probe the middle rank and its two neighbours; if
    at least two of the three are prerequisites the cut-off lies below, otherwise above.
    Everything above the final cut-off is accepted, everything below rejected."""
    pairs = sorted(ds.positive_pairs(), key=lambda p: ds.weights[p])
    pred = np.zeros((ds.n, ds.n), dtype=bool)
    if len(pairs) < 3:
        for p in pairs:
            pred[p] = oracle.ask(*p)
        return pred
    lo, hi = 0, len(pairs) - 1          # invariant: cut-off is somewhere in [lo, hi]
    answers: dict[int, bool] = {}
    for _ in range(max_steps):
        if hi - lo < 3:
            break
        mid = (lo + hi) // 2
        votes = 0
        for k in (mid - 1, mid, mid + 1):
            answers[k] = oracle.ask(*pairs[k])
            votes += answers[k]
        if votes >= 2:
            hi = mid
        else:
            lo = mid
    cut = (lo + hi) // 2
    for k, p in enumerate(pairs):
        pred[p] = answers.get(k, k > cut)
    return pred


STRATEGIES: dict[str, Strategy] = {
    "brute_force": brute_force,
    "heuristic_random": heuristic_random,
    "heuristic_by_topic": heuristic_by_topic,
    "heuristic_ordered": heuristic_ordered,
    "threshold": threshold,
    "binary_search": binary_search,
}
