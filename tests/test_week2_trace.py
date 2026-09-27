import sys

import numpy as np

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from week2_trace_coverage import (  # noqa: E402
    NOMINAL_FLOOR,
    draw_scores,
    gate_verdict,
    long_run_reference,
    resample_trace,
    standardize,
)


def test_resample_uses_only_source_values_and_requested_length():
    trace = np.arange(50, dtype=float)
    out = resample_trace(trace, 20, 4, np.random.default_rng(0))
    assert out.shape == (20,)
    assert set(np.unique(out)).issubset(set(trace))


def test_standardize_is_mean_zero_unit_sd():
    z = standardize(np.array([1.0, 2.0, 6.0, 8.0]))
    assert abs(z.mean()) < 1e-12
    assert abs(z.std() - 1.0) < 1e-12


def test_frozen_threshold_reference_fpr_is_near_the_target():
    rng = np.random.default_rng(1)
    trace = standardize(rng.normal(size=5000))
    ref = long_run_reference(trace, L=10, seed=7, n_pop=30_000)
    assert abs(ref["fpr"] - 0.01) < 0.005
    assert 0.0 < ref["recall"] < 1.0
    labels, scores = draw_scores(trace, 10, 1000, np.random.default_rng(2))
    assert labels.shape == scores.shape == (1000,)


def test_gate_rules_are_the_prespecified_floor():
    assert NOMINAL_FLOOR == 0.90
    assert gate_verdict(0.93, 0.94, 0.60).startswith("Gate 2 met")
    assert gate_verdict(0.94, 0.95, 0.94).startswith("Gate 2 partial")
    assert gate_verdict(0.88, 0.94, 0.55).startswith("Gate 2 miss")
    assert gate_verdict(0.93, 0.89, 0.55).startswith("Gate 2 miss")
