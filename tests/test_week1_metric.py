import sys
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from week1_metric_level import (  # noqa: E402
    WIDTH_FLOOR,
    aal_attack_indicator,
    excludes_zero,
    fit_panel,
    is_flip,
    metric_rows,
    width_ratio,
)


def _ar1(n, rho, seed=0):
    rng = np.random.default_rng(seed)
    return lfilter([1.0], [1.0, -rho], rng.normal(0, 1, n))


def test_aal_benign_is_normal_not_label_zero():
    attack_type = np.array(["normal", "flooding", "slow_poisoning", "normal"])
    y = aal_attack_indicator(attack_type)
    assert list(y) == [0, 1, 1, 0]


def test_flip_is_iid_exclusion_only():
    assert excludes_zero(0.02, 0.08)
    assert not excludes_zero(-0.01, 0.04)
    assert is_flip(True, False)
    assert not is_flip(True, True)
    assert not is_flip(False, False)
    assert not excludes_zero(np.nan, 0.1)


def test_width_factor_is_the_dif_floor():
    assert abs(WIDTH_FLOOR - np.sqrt(1.5)) < 1e-12
    assert abs(width_ratio(1.0, WIDTH_FLOOR) - WIDTH_FLOOR) < 1e-12


def test_ess_wilson_is_wider_under_dependence():
    alarms = (_ar1(8000, 0.95, 1) > 1.2).astype(float)
    rows = metric_rows(
        "synthetic", "flow", "iforest",
        y=np.zeros(alarms.size, int),
        score=np.where(alarms == 1, 2.0, 0.0),
        threshold=1.0,
        split_counts={"n_train": 0, "n_test": alarms.size, "n_attack_train": 0,
                      "n_attack_test": 0, "n_benign_test": alarms.size},
    )
    fpr = next(r for r in rows if r["metric"] == "fpr")
    assert fpr["series_status"] == "qualifying"
    assert fpr["width_ratio"] >= WIDTH_FLOOR
    assert fpr["naive_lo"] < fpr["estimate"] < fpr["naive_hi"]
    assert fpr["corr_lo"] < fpr["estimate"] < fpr["corr_hi"]


def test_supervised_detectors_need_both_training_classes():
    rng = np.random.default_rng(0)
    n = 2000
    X = rng.normal(size=(n, 2))
    y = np.zeros(n, int)
    y[1500:] = 1
    X[y == 1, 0] += 3
    only = fit_panel(X, y, fpr=0.01, seed=0)
    assert [d["name"] for d in only] == ["iforest"]
    assert only[0]["y"].shape == (1000,)
    assert np.isfinite(only[0]["threshold"])

    y[100:250] = 1
    X[y == 1, 0] += 3
    full = fit_panel(X, y, fpr=0.01, seed=0)
    assert [d["name"] for d in full] == ["iforest", "logreg", "rf"]
    assert all(np.isfinite(d["threshold"]) for d in full)
