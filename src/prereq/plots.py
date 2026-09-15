"""Figures for the README."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from prereq.data import Dataset  # noqa: E402

plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
BLUE, RED, GREY, GREEN, PURPLE = "#1f4e79", "#c0392b", "#7f8c8d", "#27ae60", "#8e44ad"


def plot_pareto(points: dict[str, list[tuple[int, float]]], brute: int, out: Path) -> Path:
    """questions (x) vs accuracy (y); one series per strategy family."""
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    colours = {"threshold": BLUE, "binary_search": RED, "heuristics": GREEN}
    markers = {"threshold": ".", "binary_search": "s", "heuristics": "D"}
    for name, pts in points.items():
        xs, ys = zip(*pts, strict=True)
        ax.scatter(xs, ys, s=22 if name == "threshold" else 45, color=colours.get(name, GREY),
                   marker=markers.get(name, "o"), label=name.replace("_", " "), zorder=3)
    ax.axvline(brute, color=GREY, ls="--", lw=0.9)
    ax.text(brute, 0.505, f"brute force: {brute} questions", rotation=90, va="bottom",
            ha="right", fontsize=8, color=GREY)
    ax.set_xlabel("questions asked to the expert")
    ax.set_ylabel("accuracy over all ordered pairs")
    ax.set_ylim(0.5, 1.005)
    ax.set_title("Accuracy against expert effort", loc="left")
    ax.legend(frameon=False, fontsize=8, loc="center right")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_weights(ds: Dataset, out: Path) -> Path:
    truth = ds.closure()
    w = ds.weights
    off = ~np.eye(ds.n, dtype=bool)
    pos = (w > 0) & off
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    ax = axes[0]
    bins = np.linspace(0, np.percentile(w[pos], 97), 40)
    ax.hist(w[pos & ~truth], bins=bins, color=GREY, alpha=0.8, label="not a prerequisite")
    ax.hist(w[pos & truth], bins=bins, color=BLUE, alpha=0.8, label="prerequisite (closure)")
    ax.set_xlabel("weight (positive direction only)")
    ax.set_ylabel("pairs")
    ax.set_title("Weights separate the classes only partly", loc="left")
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    order = np.argsort(-w[pos])
    ranked_truth = truth[pos][order]
    ax.plot(np.arange(1, len(order) + 1), np.cumsum(ranked_truth) / truth[off].sum(), color=BLUE)
    ax.plot([0, len(order)], [0, 1], color=GREY, ls="--", lw=0.9)
    ax.set_xlabel("pairs, ranked by weight")
    ax.set_ylabel("share of true prerequisites recovered")
    ax.set_title("Ranking quality of the weights", loc="left")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_graph(ds: Dataset, out: Path) -> Path:
    """Layered drawing of the ground-truth DAG (direct edges), basic topics at the bottom."""
    direct = ds.direct
    n = ds.n
    depth = np.zeros(n, dtype=int)
    for _ in range(n):
        for i, j in zip(*np.nonzero(direct), strict=True):
            depth[j] = max(depth[j], depth[i] + 1)
    layers: dict[int, list[int]] = {}
    for t in range(n):
        layers.setdefault(int(depth[t]), []).append(t)
    pos = {}
    for d, ts in layers.items():
        ts = sorted(ts, key=lambda t: ds.topics[t])
        for k, t in enumerate(ts):
            pos[t] = ((k + 0.5) / len(ts), d)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for i, j in zip(*np.nonzero(direct), strict=True):
        (x0, y0), (x1, y1) = pos[i], pos[j]
        ax.annotate("", xy=(x1, y1 - 0.08), xytext=(x0, y0 + 0.08),
                    arrowprops=dict(arrowstyle="-|>", color="#999999", lw=0.7, alpha=0.7))
    for t, (x, y) in pos.items():
        ax.text(x, y, ds.topics[t].replace(" and ", " & "), ha="center", va="center", fontsize=7.5,
                bbox=dict(boxstyle="round,pad=0.3", fc="#eaf1f8", ec=BLUE, lw=0.8), zorder=3)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.5, max(layers) + 0.5)
    ax.set_yticks(range(max(layers) + 1))
    ax.set_ylabel("depth (longest prerequisite chain)")
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.grid(False)
    ax.set_title(f"Ground truth: {int(direct.sum())} direct prerequisites among {n} linear-algebra "
                 f"micro-topics ({int(ds.closure().sum())} in the transitive closure)", loc="left")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out
