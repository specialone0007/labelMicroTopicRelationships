"""The simulated expert. Answers "is i a prerequisite of j?" from the ground truth and counts
how many questions it was asked; that count is the cost every strategy is trying to minimise.
"""

from __future__ import annotations

import numpy as np


class Oracle:
    def __init__(self, truth: np.ndarray):
        self._truth = truth
        self.questions = 0
        self.asked: set[tuple[int, int]] = set()

    def ask(self, i: int, j: int) -> bool:
        if i == j:
            raise ValueError("a topic is not its own prerequisite")
        key = (i, j)
        if key not in self.asked:      # repeating a question is free: the expert already answered
            self.asked.add(key)
            self.questions += 1
        return bool(self._truth[i, j])
