"""Datasets: a list of micro-topics, a weight matrix and the ground-truth prerequisite graph.

`weights[i, j]` is the model's score for "topic i is a prerequisite of topic j"; positive means
likely, negative means the reverse direction is likely, so the matrix is antisymmetric. The
ground truth is a directed acyclic graph of *direct* prerequisites; its transitive closure is
also available because an expert who knows A → B and B → C would not need to be asked about
A → C.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Dataset:
    name: str
    topics: tuple[str, ...]
    weights: np.ndarray       # (n, n) float, weights[i, j] = score for i -> j
    direct: np.ndarray        # (n, n) bool, direct[i, j] = i is a listed prerequisite of j
    excluded: tuple[tuple[str, str], ...] = ()   # mutual pairs dropped from the listing

    @property
    def n(self) -> int:
        return len(self.topics)

    def index(self, topic: str) -> int:
        return self.topics.index(topic)

    def closure(self) -> np.ndarray:
        """Transitive closure of the direct graph (Warshall)."""
        r = self.direct.copy()
        for k in range(self.n):
            r |= r[:, [k]] & r[[k], :]
        return r

    def truth(self, transitive: bool) -> np.ndarray:
        return self.closure() if transitive else self.direct

    def ordered_pairs(self) -> list[tuple[int, int]]:
        return [(i, j) for i in range(self.n) for j in range(self.n) if i != j]

    def positive_pairs(self) -> list[tuple[int, int]]:
        """Ordered pairs with a positive weight, i.e. the direction the model thinks likely."""
        return [(i, j) for i, j in self.ordered_pairs() if self.weights[i, j] > 0]

    def advanced_to_basic(self) -> list[int]:
        """Topics sorted by weighted in-degree, most advanced (most prerequisites) first."""
        score = np.where(self.weights > 0, self.weights, 0).sum(axis=0)
        return sorted(range(self.n), key=lambda j: -score[j])


def parse_prerequisites(text: str, topics: tuple[str, ...]) -> np.ndarray:
    """`*topic` starts a block; each following line names one prerequisite of that topic."""
    idx = {t: i for i, t in enumerate(topics)}
    direct = np.zeros((len(topics), len(topics)), dtype=bool)
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("*"):
            current = line[1:].strip()
            if current not in idx:
                raise ValueError(f"unknown topic {current!r}")
        else:
            if current is None:
                raise ValueError("prerequisite line before any *topic header")
            if line not in idx:
                raise ValueError(f"unknown prerequisite {line!r} under {current!r}")
            direct[idx[line], idx[current]] = True
    return direct


def parse_weights(text: str, n: int) -> np.ndarray:
    """Whitespace-separated floats, n*n of them, laid out so that value k = n*j + i is the
    weight for i -> j (the 2020 files were written column-major)."""
    vals = np.array([float(x) for x in text.split()], dtype=float)
    if vals.size != n * n:
        raise ValueError(f"expected {n * n} weights, found {vals.size}")
    return vals.reshape(n, n).T


def load_dataset(name: str = "linear-algebra", root: Path | str = DATA_DIR) -> Dataset:
    d = Path(root) / name
    topics = tuple(line.strip() for line in (d / "microtopics.txt").read_text(encoding="utf-8")
                   .splitlines() if line.strip())
    weights = parse_weights((d / "weights.txt").read_text(encoding="utf-8"), len(topics))
    direct = parse_prerequisites((d / "prerequisites.txt").read_text(encoding="utf-8"), topics)
    # A pair listed in both directions cannot be a prerequisite relationship in either; the
    # expert lists are hand-written, so report such pairs and leave them out of the truth.
    mutual = direct & direct.T
    excluded = tuple(sorted((topics[i], topics[j]) for i, j in zip(*np.nonzero(mutual),
                                                                    strict=True) if i < j))
    direct = direct & ~mutual
    ds = Dataset(name, topics, weights, direct, excluded)
    if np.any(np.diag(ds.closure())):
        raise ValueError("prerequisite graph has a cycle longer than two topics")
    return ds
