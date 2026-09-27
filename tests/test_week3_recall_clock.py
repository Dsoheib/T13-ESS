import sys

import numpy as np
from scipy.signal import lfilter

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from t13.dif import integrated_autocorrelation_time  # noqa: E402
from week3_recall_clock import (  # noqa: E402
    close_enough,
    geyer_tau_from_rho,
    missing_clock_bounds,
    pairwise_rho,
)


def _ar1(n, rho, seed):
    rng = np.random.default_rng(seed)
    return lfilter([1.0], [1.0, -rho], rng.normal(size=n))


def test_complete_series_matches_geyer():
    x = (_ar1(4000, 0.8, 0) > 0).astype(float)
    tau_ref, _ = integrated_autocorrelation_time(x, "geyer", guard=False)
    tau = geyer_tau_from_rho(pairwise_rho(x, min_pairs=3))
    assert abs(tau - tau_ref) < 1e-6


def test_missing_clock_interval_contains_a_constant_rate():
    z = np.full(200, np.nan)
    z[::2] = 1.0
    lo, hi = missing_clock_bounds(z)
    assert lo <= 1.0 <= hi


def test_close_rule_uses_two_combined_standard_errors():
    ok, gap, tol = close_enough(0.50, 0.02, 0.53, 0.02)
    assert ok and abs(gap - 0.03) < 1e-12
    assert abs(tol - 2 * np.hypot(0.02, 0.02)) < 1e-12
    assert not close_enough(0.50, 0.02, 0.70, 0.02)[0]
