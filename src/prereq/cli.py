"""prereq: how many expert questions does it take to label a prerequisite graph?

  prereq info                          dataset summary
  prereq run  <strategy> [--lower L --upper U] [--seed S] [--direct]
  prereq ask  <strategy>               interactive: you are the expert
  prereq bench                         every strategy + threshold grid -> results/, docs/figures/
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from prereq import plots
from prereq.data import load_dataset
from prereq.evaluate import repeat, run, score
from prereq.oracle import Oracle
from prereq.strategies import STRATEGIES

ROOT = Path(__file__).resolve().parents[2]


def cmd_info(a) -> int:
    ds = load_dataset(a.dataset)
    print(f"{ds.name}: {ds.n} topics, {int(ds.direct.sum())} direct prerequisites, "
          f"{int(ds.closure().sum())} in closure, {len(ds.positive_pairs())} positive-weight "
          f"pairs, {ds.n * (ds.n - 1)} ordered pairs")
    print("advanced -> basic:", ", ".join(ds.topics[t] for t in ds.advanced_to_basic()[:6]), "...")
    if ds.excluded:
        both = "; ".join(f"{a} <-> {b}" for a, b in ds.excluded)
        print("listed in both directions, excluded:", both)
    return 0


def _params(a) -> dict:
    p = {}
    if a.lower is not None:
        p["lower"] = a.lower
    if a.upper is not None:
        p["upper"] = a.upper
    return p


def cmd_run(a) -> int:
    ds = load_dataset(a.dataset)
    if a.strategy == "threshold" and (a.lower is None or a.upper is None):
        print("threshold needs --lower and --upper", file=sys.stderr)
        return 2
    o = run(ds, a.strategy, seed=a.seed, transitive_truth=not a.direct, **_params(a))
    print(f"{o.strategy} {o.params}: {o.questions} questions, accuracy {o.accuracy:.3f}, "
          f"precision {o.precision:.3f}, recall {o.recall:.3f}")
    return 0


class HumanOracle(Oracle):
    def __init__(self, ds):
        super().__init__(np.zeros((ds.n, ds.n), dtype=bool))
        self.ds = ds

    def ask(self, i, j):
        if (i, j) in self.asked:
            return self._truth[i, j]
        self.asked.add((i, j))
        self.questions += 1
        ans = input(f"Q{self.questions}: is '{self.ds.topics[i]}' a prerequisite of "
                    f"'{self.ds.topics[j]}'? [y/n] ").strip().lower()
        self._truth[i, j] = ans.startswith("y")
        return bool(self._truth[i, j])


def cmd_ask(a) -> int:
    ds = load_dataset(a.dataset)
    if a.strategy == "threshold" and (a.lower is None or a.upper is None):
        print("threshold needs --lower and --upper", file=sys.stderr)
        return 2
    oracle = HumanOracle(ds)
    pred = STRATEGIES[a.strategy](ds, oracle, rng=np.random.default_rng(a.seed), **_params(a))
    acc, prec, rec = score(pred, ds.closure())
    print(f"\n{oracle.questions} questions asked. Against the bundled ground truth: "
          f"accuracy {acc:.3f}, precision {prec:.3f}, recall {rec:.3f}")
    for i, j in zip(*np.nonzero(pred), strict=True):
        print(f"  {ds.topics[i]}  ->  {ds.topics[j]}")
    return 0


def cmd_bench(a) -> int:
    ds = load_dataset(a.dataset)
    res_dir, fig_dir = ROOT / "results", ROOT / "docs" / "figures"
    res_dir.mkdir(exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    brute = run(ds, "brute_force").questions
    print(f"brute force: {brute} questions")
    rows.append(["brute_force", "", brute, 0.0, 1.0])
    heur_pts = []
    for s in ("heuristic_random", "heuristic_by_topic", "heuristic_ordered"):
        qm, qs, am = repeat(ds, s, seeds=a.seeds)
        print(f"{s:<20} {qm:6.1f} ± {qs:4.1f} questions, accuracy {am:.3f}")
        rows.append([s, "", round(qm, 1), round(qs, 1), round(am, 4)])
        heur_pts.append((round(qm), am))
    bs = run(ds, "binary_search")
    print(f"binary_search        {bs.questions:6d} questions, accuracy {bs.accuracy:.3f}")
    rows.append(["binary_search", "", bs.questions, 0.0, round(bs.accuracy, 4)])
    thr_pts = []
    grid = [0, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 500, 1000]
    best = None
    for lo in grid:
        for up in grid:
            if up < lo:
                continue
            o = run(ds, "threshold", lower=lo, upper=up)
            rows.append(["threshold", f"lower={lo},upper={up}", o.questions, 0.0,
                         round(o.accuracy, 4)])
            thr_pts.append((o.questions, o.accuracy))
            if best is None or (o.accuracy, -o.questions) > (best[0].accuracy, -best[0].questions):
                best = (o, lo, up)
    print(f"threshold grid: {len(thr_pts)} settings; best accuracy {best[0].accuracy:.3f} at "
          f"lower={best[1]}, upper={best[2]} with {best[0].questions} questions")
    with (res_dir / "benchmark.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strategy", "params", "questions_mean", "questions_std", "accuracy"])
        w.writerows(rows)
    plots.plot_pareto({"threshold": thr_pts, "binary_search": [(bs.questions, bs.accuracy)],
                       "heuristics": heur_pts}, brute, fig_dir / "accuracy-vs-questions.png")
    plots.plot_weights(ds, fig_dir / "weights.png")
    plots.plot_graph(ds, fig_dir / "ground-truth.png")
    print(f"wrote {res_dir / 'benchmark.csv'} and 3 figures to {fig_dir}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="prereq", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default="linear-algebra")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("info")
    s.set_defaults(fn=cmd_info)
    for name, fn in (("run", cmd_run), ("ask", cmd_ask)):
        s = sub.add_parser(name)
        s.add_argument("strategy", choices=list(STRATEGIES))
        s.add_argument("--lower", type=float)
        s.add_argument("--upper", type=float)
        s.add_argument("--seed", type=int, default=0)
        s.add_argument("--direct", action="store_true",
                       help="score against direct edges instead of the transitive closure")
        s.set_defaults(fn=fn)
    s = sub.add_parser("bench")
    s.add_argument("--seeds", type=int, default=100)
    s.set_defaults(fn=cmd_bench)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
