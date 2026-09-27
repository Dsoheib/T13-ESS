"""Naive and dependence-corrected confidence intervals for detection metrics.

Routes: plug-in ESS; moving-block bootstrap (Kunsch 1989, primary); stationary bootstrap
(Politis & Romano 1994); episode (cluster) bootstrap over contiguous label runs; block
jackknife AUC (serial analogue of DeLong / Obuchowski clustered ROC); paired difference
on shared blocks (survival test).

Interval type: 'percentile' (default) or 'basic' (2*est - percentile, better for skewed
statistics near 0/1 such as recall at low FPR). Every bootstrap routine returns the
number of resampled blocks; fewer than MIN_BLOCKS is flagged as unreliable.
"""
from __future__ import annotations
import warnings
import numpy as np
from scipy import stats as st
from scipy.stats import rankdata
from .dif import block_length, integrated_autocorrelation_time, n_blocks

MIN_BLOCKS = 10


def recall_at_fpr(y, s, fpr=0.01):
    y = np.asarray(y).astype(bool); s = np.asarray(s, float)
    neg = s[~y]
    if neg.size == 0 or y.sum() == 0:
        return np.nan
    thr = np.quantile(neg, 1.0 - fpr)
    return float(np.mean(s[y] > thr))


def recall_at_threshold(thr):
    def f(y, s):
        y = np.asarray(y).astype(bool)
        return float(np.mean(np.asarray(s)[y] > thr)) if y.any() else np.nan
    return f


def fpr_at_threshold(thr):
    """False-positive rate at a fixed operating point: the alarm-rate quantity an operator
    actually budgets. Class-conditional, so prevalence-invariant."""
    def f(y, s):
        y = np.asarray(y).astype(bool)
        return float(np.mean(np.asarray(s)[~y] > thr)) if (~y).any() else np.nan
    return f


def wilson(k, n, alpha=0.05):
    """Wilson score interval for a proportion (used for the audit's own prevalence numbers)."""
    if n == 0:
        return np.nan, np.nan, np.nan
    z = st.norm.ppf(1 - alpha / 2); p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c, c - h, c + h


def wilson_ess_ci(indicator, alpha=0.05, rule="geyer"):
    """Wilson interval for a rare-event proportion (FPR ~ 1%) with n replaced by n_eff.
    The normal ESS plug-in is poor near 0; this is the recommended FPR interval."""
    v = np.asarray(indicator, float); n = v.size
    tau, _ = integrated_autocorrelation_time(v, rule); n_eff = n / tau
    c, lo, hi = wilson(v.sum() / n * n_eff, n_eff, alpha)
    return v.mean(), lo, hi, n_eff


def auc(y, s):
    """Mann-Whitney AUC (rank-based, ties averaged)."""
    y = np.asarray(y).astype(bool); s = np.asarray(s, float)
    n1 = int(y.sum()); n0 = y.size - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def accuracy(y, p):
    return float(np.mean(np.asarray(y) == np.asarray(p)))


def _interval(boots, est, alpha, kind):
    lo, hi = np.nanpercentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    if kind == "basic":
        return 2 * est - hi, 2 * est - lo
    return lo, hi

# ---------------- naive ----------------

def naive_normal_ci(values, alpha=0.05):
    v = np.asarray(values, float); n = v.size
    m = v.mean(); se = v.std(ddof=1) / np.sqrt(n); z = st.norm.ppf(1 - alpha / 2)
    return m, m - z * se, m + z * se


def naive_iid_bootstrap_ci(y, s, stat, B=1000, alpha=0.05, rng=None, kind="percentile"):
    rng = np.random.default_rng(rng)
    y = np.asarray(y); s = np.asarray(s); n = y.size
    est = stat(y, s); boots = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n); boots[b] = stat(y[idx], s[idx])
    lo, hi = _interval(boots, est, alpha, kind)
    return est, lo, hi

# ---------------- corrected ----------------

def ess_plugin_ci(values, alpha=0.05, rule="geyer"):
    v = np.asarray(values, float); n = v.size
    tau, _ = integrated_autocorrelation_time(v, rule); n_eff = n / tau
    m = v.mean(); se = v.std(ddof=1) / np.sqrt(n_eff); z = st.norm.ppf(1 - alpha / 2)
    return m, m - z * se, m + z * se, n_eff


def _mbb_indices(n, L, rng):
    nb = int(np.ceil(n / L))
    starts = rng.integers(0, n - L + 1, nb)
    return (starts[:, None] + np.arange(L)[None, :]).ravel()[:n]


def _sb_indices(n, L, rng):
    """Stationary bootstrap indices (vectorised): geometric block lengths, mean L, circular."""
    p = 1.0 / L
    m = int(np.ceil(n / L)) + 8
    while True:
        lengths = rng.geometric(p, m)
        if lengths.sum() >= n:
            break
        m *= 2
    starts = rng.integers(0, n, m)
    offs = np.concatenate([np.arange(l) for l in lengths])
    base = np.repeat(starts, lengths)
    return ((base + offs) % n)[:n]


def _choose_L(L, y, s_list):
    if L is not None:
        return L
    return block_length(np.asarray(y, float), *[np.asarray(s, float) for s in s_list])


def block_bootstrap_ci(y, s, stat, L=None, B=1000, alpha=0.05, method="moving", rng=None,
                       kind="percentile"):
    """Block bootstrap CI for stat(y, s). L defaults to the slowest of (labels, scores).
    Returns (est, lo, hi, L, nb, reliable)."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y); s = np.asarray(s); n = y.size
    L = _choose_L(L, y, [s]); nb = n_blocks(n, L)
    gen = _mbb_indices if method == "moving" else _sb_indices
    est = stat(y, s); boots = np.empty(B)
    for b in range(B):
        idx = gen(n, L, rng); boots[b] = stat(y[idx], s[idx])
    lo, hi = _interval(boots, est, alpha, kind)
    return est, lo, hi, L, nb, nb >= MIN_BLOCKS


def subsampling_ci(y, s, stat, b=None, alpha=0.05, rate=0.5, max_blocks=2000, rng=None):
    """Subsampling interval (Politis, Romano & Wolf 1999). Evaluates stat on overlapping
    contiguous blocks of length b and uses the empirical law of n**rate * (theta_b - theta_n)
    rescaled by (b/n)**rate. Valid under mixing without a smoothness requirement on stat,
    and (with the right rate) under long-range dependence — the robustness route when the
    block bootstrap under-covers for AUC. Returns (est, lo, hi, b, n_sub, reliable)."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y); s = np.asarray(s); n = y.size
    if b is None:
        b = int(max(50, min(n // 4, np.ceil(n ** 0.6))))
    est = stat(y, s)
    starts = np.arange(0, n - b + 1)
    if starts.size > max_blocks:
        starts = np.sort(rng.choice(starts, max_blocks, replace=False))
    vals = np.array([stat(y[i:i + b], s[i:i + b]) for i in starts])
    vals = vals[~np.isnan(vals)]
    if vals.size < MIN_BLOCKS:
        return est, np.nan, np.nan, b, vals.size, False
    z = (b ** rate) * (vals - est)
    qlo, qhi = np.percentile(z, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    lo = est - qhi / (n ** rate); hi = est - qlo / (n ** rate)
    return est, lo, hi, b, vals.size, True


def episodes(y):
    """Contiguous runs of equal label -> list of (start, end) index pairs."""
    y = np.asarray(y).astype(int)
    change = np.flatnonzero(np.diff(y)) + 1
    starts = np.concatenate([[0], change]); ends = np.concatenate([change, [y.size]])
    return list(zip(starts, ends))


def episode_bootstrap_ci(y, s, stat, B=1000, alpha=0.05, rng=None, kind="percentile"):
    """Cluster bootstrap over contiguous label runs (attack campaigns and benign gaps).
    Natural correction when episodes are the unit of independence; ties to episode-level
    metrics. Returns (est, lo, hi, n_episodes, reliable)."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y); s = np.asarray(s)
    eps = episodes(y); E = len(eps)
    ep_arrays = [np.arange(a, b_) for a, b_ in eps]   # precompute once (was re-aranged per bootstrap)
    est = stat(y, s); boots = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, E, E)
        idx = np.concatenate([ep_arrays[i] for i in pick])
        boots[b] = stat(y[idx], s[idx])
    lo, hi = _interval(boots, est, alpha, kind)
    return est, lo, hi, E, E >= 2 * MIN_BLOCKS


def block_jackknife_auc(y, s, L=None, alpha=0.05, max_blocks=50):
    y = np.asarray(y); s = np.asarray(s); n = y.size
    L = _choose_L(L, y, [s])
    # cap the number of leave-one-block-out refits: a delete-one-block jackknife with thousands
    # of length-2 blocks (which happens when the score is near-independent, L ~ 2) is both
    # O(n^2) and statistically degenerate. Enforce nb <= max_blocks by growing L if needed.
    L = max(L, int(np.ceil(n / max_blocks)))
    nb = n_blocks(n, L)
    full = auc(y, s); reps = []
    for b in range(nb):
        m = np.ones(n, bool); m[b * L:(b + 1) * L] = False
        v = auc(y[m], s[m])
        if not np.isnan(v):
            reps.append(v)
    reps = np.asarray(reps); g = reps.size
    if g < 2:
        return full, np.nan, np.nan, L, nb, False
    se = np.sqrt((g - 1) / g * np.sum((reps - reps.mean()) ** 2))
    z = st.norm.ppf(1 - alpha / 2)
    return full, full - z * se, full + z * se, L, nb, nb >= MIN_BLOCKS


def paired_difference_ci(y, s_a, s_b, stat, L=None, B=1000, alpha=0.05, rng=None,
                         kind="percentile"):
    """Block-bootstrap CI and two-sided p for stat(A)-stat(B) on SHARED blocks.
    L from the slowest of (labels, scores A, scores B)."""
    rng = np.random.default_rng(rng)
    y = np.asarray(y); s_a = np.asarray(s_a); s_b = np.asarray(s_b); n = y.size
    L = _choose_L(L, y, [s_a, s_b]); nb = n_blocks(n, L)
    d0 = stat(y, s_a) - stat(y, s_b); boots = np.empty(B)
    for b in range(B):
        idx = _mbb_indices(n, L, rng)
        boots[b] = stat(y[idx], s_a[idx]) - stat(y[idx], s_b[idx])
    lo, hi = _interval(boots, d0, alpha, kind)
    p = 2 * min(np.mean(boots <= 0), np.mean(boots >= 0))
    return d0, lo, hi, L, nb, float(min(1.0, p)), nb >= MIN_BLOCKS
