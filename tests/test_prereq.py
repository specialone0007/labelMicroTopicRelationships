import numpy as np
import pytest

from prereq import STRATEGIES, Dataset, Oracle, load_dataset, run, score
from prereq.data import parse_prerequisites, parse_weights


@pytest.fixture(scope="module")
def ds() -> Dataset:
    return load_dataset("linear-algebra")


def toy() -> Dataset:
    topics = ("a", "b", "c", "d")
    direct = parse_prerequisites("*b\na\n*c\nb\n*d\nc\n", topics)   # chain a->b->c->d
    w = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            if i < j:
                w[i, j] = 10.0 * (j - i)
                w[j, i] = -w[i, j]
    return Dataset("toy", topics, w, direct)


def test_dataset_shape(ds):
    assert ds.n == 29
    assert ds.weights.shape == (29, 29)
    assert np.allclose(ds.weights, -ds.weights.T)          # antisymmetric
    assert int(ds.direct.sum()) == 169                       # 171 listed, one mutual pair dropped
    assert ds.excluded == (("determinant", "Gaussian elimination"),)
    assert not np.any(np.diag(ds.closure()))
    assert ds.closure().sum() >= ds.direct.sum()
    assert not (ds.direct & ds.direct.T).any()


def test_weight_orientation_matches_truth(ds):
    """Positive weights should point the way the ground truth does far more often than not."""
    off = ~np.eye(ds.n, dtype=bool)
    truth = ds.closure()
    agree = (ds.weights[truth & off] > 0).mean()
    assert agree > 0.7


def test_parse_errors():
    with pytest.raises(ValueError):
        parse_prerequisites("*zzz\na\n", ("a", "b"))
    with pytest.raises(ValueError):
        parse_prerequisites("a\n", ("a", "b"))
    with pytest.raises(ValueError):
        parse_weights("1 2 3", 2)


def test_closure_of_chain():
    t = toy()
    assert t.direct.sum() == 3 and t.closure().sum() == 6
    assert t.closure()[0, 3]


def test_oracle_counts_unique_questions():
    o = Oracle(toy().closure())
    assert o.ask(0, 1) is True and o.ask(1, 0) is False
    o.ask(0, 1)
    assert o.questions == 2
    with pytest.raises(ValueError):
        o.ask(1, 1)


@pytest.mark.parametrize("name", [s for s in STRATEGIES if s != "threshold"])
def test_strategies_run_on_toy(name):
    t = toy()
    o = Oracle(t.closure())
    pred = STRATEGIES[name](t, o, rng=np.random.default_rng(0))
    assert pred.shape == (4, 4)
    assert o.questions <= 12


def test_brute_force_is_exact(ds):
    o = run(ds, "brute_force")
    assert o.questions == 29 * 28 and o.accuracy == 1.0


def test_heuristics_exact_and_cheaper(ds):
    brute = run(ds, "brute_force").questions
    for s in ("heuristic_random", "heuristic_by_topic", "heuristic_ordered"):
        o = run(ds, s, seed=3)
        assert o.accuracy == 1.0, s          # implication never contradicts a transitive truth
        assert o.questions < brute, s


def test_threshold_extremes(ds):
    ask_all = run(ds, "threshold", lower=-1, upper=1e9)   # ask every positive-weight pair
    assert ask_all.questions == len(ds.positive_pairs())
    assert ask_all.precision == 1.0                          # asked pairs are answered exactly
    assert ask_all.accuracy > 0.9                            # misses only the mis-signed weights
    ask_none = run(ds, "threshold", lower=1e9, upper=1e9)
    assert ask_none.questions == 0
    assert 0.5 < ask_none.accuracy < 1.0


def test_binary_search_bounds(ds):
    o = run(ds, "binary_search")
    assert 0 < o.questions <= 3 * 20
    assert 0.5 < o.accuracy <= 1.0


def test_score():
    truth = np.array([[0, 1], [0, 0]], dtype=bool)
    acc, prec, rec = score(truth, truth)
    assert (acc, prec, rec) == (1.0, 1.0, 1.0)
    acc, prec, rec = score(np.zeros((2, 2), bool), truth)
    assert acc == 0.5 and rec == 0.0
