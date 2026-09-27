import sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
from scipy.signal import lfilter
from t13.dif import integrated_autocorrelation_time, block_length, RULES, reliability
from t13.ci import ess_plugin_ci, naive_normal_ci, _mbb_indices, _sb_indices, episodes, auc
from t13.sim import fgn, markov_labels


def ar1(n, rho, seed=0):
    rng = np.random.default_rng(seed); z = rng.normal(0, 1, n)
    return lfilter([1.0], [1.0, -rho], z)


def test_acf_fft_matches_direct():
    """acf is FFT-based (O(n log n)); assert it matches a direct O(n^2) computation to 1e-10
    on a 5000-point AR(1), so the fast path is verified correct (P26)."""
    from t13.dif import acf
    x = ar1(5000, 0.8)
    fast = acf(x, 40)
    xc = x - x.mean(); var = np.dot(xc, xc) / xc.size
    direct = np.array([np.dot(xc[:xc.size - k], xc[k:]) / xc.size / var for k in range(41)])
    assert np.max(np.abs(fast - direct)) < 1e-10


def test_all_rules_near_ar1_closed_form():
    x = ar1(200_000, 0.8)
    for r in ("geyer", "batch", "ar1", "zero"):
        tau, _ = integrated_autocorrelation_time(x, r)
        assert abs(tau - 9.0) / 9.0 < 0.08, (r, tau)


def test_iid_has_dif_near_one():
    x = ar1(100_000, 0.0)
    for r in RULES:
        assert integrated_autocorrelation_time(x, r)[0] < 1.15


def test_ess_interval_wider_under_dependence():
    x = ar1(20_000, 0.9)
    _, lo0, hi0 = naive_normal_ci(x); _, lo1, hi1, n_eff = ess_plugin_ci(x)
    assert (hi1 - lo1) > 2 * (hi0 - lo0) and n_eff < x.size / 5


def test_block_length_uses_slowest_series():
    fast = ar1(5000, 0.2, 1); slow = ar1(5000, 0.95, 2)
    assert block_length(fast, slow) > block_length(fast) and block_length(fast, slow) <= int(5000 ** (2 / 3))


def test_bootstrap_index_generators():
    rng = np.random.default_rng(0); n, L = 1000, 25
    i1 = _mbb_indices(n, L, rng); assert i1.size == n and i1.min() >= 0 and i1.max() < n
    i2 = _sb_indices(n, L, rng); assert i2.size == n and i2.min() >= 0 and i2.max() < n


def test_episodes_partition():
    y = np.array([0, 0, 1, 1, 1, 0, 1])
    e = episodes(y); assert e == [(0, 2), (2, 5), (5, 6), (6, 7)]


def test_markov_labels_prevalence():
    rng = np.random.default_rng(0)
    m = np.mean([markov_labels(100_000, 0.995, 0.05, rng).mean() for _ in range(30)])
    assert abs(m - 0.05) < 0.005


def test_fgn_lag1_matches_theory():
    rng = np.random.default_rng(0); H = 0.8; x = fgn(100_000, H, rng)
    r1 = np.corrcoef(x[:-1], x[1:])[0, 1]; assert abs(r1 - 0.5 * (2 ** (2 * H) - 2)) < 0.02


def test_auc_matches_sklearn():
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(0); y = rng.integers(0, 2, 500); s = rng.normal(size=500) + y
    assert abs(auc(y, s) - roc_auc_score(y, s)) < 1e-9


def test_reliability_flags():
    x = ar1(300, 0.98)
    assert not reliability(x)["reliable"]


def test_politis_white_reasonable():
    from t13.dif import politis_white_block_length
    x = ar1(20_000, 0.8, 5); Lm, Ls = politis_white_block_length(x)
    assert 3 <= Lm <= 300 and 3 <= Ls <= 300
    xi = ar1(20_000, 0.0, 6); Lm0, _ = politis_white_block_length(xi)
    assert Lm0 < Lm


def test_wilson():
    from t13.ci import wilson
    c, lo, hi = wilson(30, 40); assert lo < 0.75 < hi and 0.55 < lo and hi < 0.9


# test_iid_coverage_smoke removed 2026-09-19: it validated the contaminated (wrong-estimand)
# sim.run path with a too-loose >=0.75 gate. Replaced by tests/test_control_guard.py, which
# scores the threshold-conditional estimand and fails on injected miscoverage.


def test_reference_scores_runs():
    from t13.datasets import to_grain, dif_table
    rng = np.random.default_rng(0); n = 3000
    df = pd.DataFrame({"t": np.arange(n), "y": (rng.random(n) < 0.05).astype(int),
                       "f1": rng.normal(size=n), "f2": rng.normal(size=n)})
    df.loc[df.y == 1, "f1"] += 2
    tab = dif_table(df, "synthetic", grains=("flow", "window:10"))
    assert {"label", "feature", "detector"} <= set(tab.family) and tab.dif_geyer.min() >= 1.0


def test_subsampling_and_conditional_truth():
    from t13.ci import subsampling_ci, auc
    from t13.sim import conditional_truth, generate
    rng = np.random.default_rng(0); a, s = generate(6000, rho=0.5, p_stay=0.05, prevalence=0.1, rng=rng)
    est, lo, hi, b, nsub, ok = subsampling_ci(a, s, auc, rng=rng); assert ok and lo < est < hi
    ct = conditional_truth(thr=2.0, mu=2.0, rho=0.0); assert abs(ct["recall"] - 0.5) < 1e-9


def test_wilson_ess_and_agreement_and_dif_ci():
    from t13.ci import wilson_ess_ci
    from t13.dif import agreement, dif_ci
    x = (ar1(20_000, 0.9, 7) > 2.0).astype(float)
    m, lo, hi, n_eff = wilson_ess_ci(x); assert lo <= m <= hi and 0 <= lo and n_eff < x.size
    y = ar1(20_000, 0.8, 8); ag = agreement(y); assert ag["agree"]
    t0, tlo, thi, ok = dif_ci(y); assert ok and tlo <= 9.5 and thi >= 8.5 and 5 < t0 < 14
