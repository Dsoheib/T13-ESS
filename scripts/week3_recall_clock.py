"""Week 3 — recall clock sensitivity.

The reported recall interval drops benign rows and estimates the autocorrelation
on that attack subsequence. This run keeps those replicates and builds a second
interval on the same hit indicators, with benign rows treated as missing on the
original test-set clock. Pairwise products at lag k use only positions that are
both attacks. The Geyer truncation is otherwise the one in src/t13/dif.py.
The normal ESS plug-in then uses n_attack / tau.

Scenario: the short-memory campaign cell (bg_ar__lab_campaign). Threshold learned
on the training half. Target: the Gaussian threshold-conditional recall, the same
target as the coverage simulation. n in {5000, 20000}, R=500. Both clocks are
scored on every replicate.

Pre-specified rule. The objection is closed at a sample size when the absolute
difference of the two unconditional coverages is at most twice their combined
Monte Carlo standard error. The claims keep the subsequence clock either way.
A lag with fewer than 30 observed pairs stops the autocorrelation sum.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from t13.ci import ess_plugin_ci  # noqa: E402
from t13.dif import integrated_autocorrelation_time  # noqa: E402
from t13.sim import SCENARIOS, _mc_se, _try, conditional_truth, generate  # noqa: E402

SCENARIO = "bg_ar__lab_campaign"
SIZES = (5000, 20000)
R = 500
FPR = 0.01
MIN_PAIRS = 30
SEED = 20260923


def pairwise_rho(z, min_pairs=MIN_PAIRS):
    """Biased ACF with pairwise deletion. rho[0] = 1. Missing lags are NaN."""
    z = np.asarray(z, float)
    n = z.size
    obs = np.isfinite(z)
    n_obs = int(obs.sum())
    max_lag = min(n - 2, max(50, int(20 * n ** 0.5)))
    rho = np.full(max_lag + 1, np.nan)
    rho[0] = 1.0
    if n_obs < 3:
        return rho
    u = np.zeros(n)
    u[obs] = z[obs] - z[obs].mean()
    var = float(np.dot(u, u))
    if var == 0.0:
        rho[1:] = 0.0
        return rho
    nfft = 1 << (2 * n - 1).bit_length()

    def linear_corr(a):
        f = np.fft.rfft(a, nfft)
        return np.fft.irfft(f * np.conj(f), nfft)[:n]

    prod = linear_corr(u)
    count = linear_corr(obs.astype(float))
    for k in range(1, max_lag + 1):
        if count[k] < min_pairs:
            break
        rho[k] = prod[k] / var
    return rho


def geyer_tau_from_rho(rho):
    """Geyer initial-positive-sequence sum. A non-finite lag ends the sum."""
    s = 0.0
    m = 0
    max_lag = len(rho) - 1
    while True:
        i, j = 2 * m, 2 * m + 1
        if j > max_lag or not np.isfinite(rho[i]) or not np.isfinite(rho[j]):
            break
        g = float(rho[i] + rho[j])
        if g <= 0.0:
            break
        s += g
        m += 1
    return max(1.0, -1.0 + 2.0 * s)


def normal_ess_bounds(values, tau):
    v = np.asarray(values, float)
    if v.size < 3 or not np.isfinite(tau) or tau <= 0:
        return np.nan, np.nan
    n_eff = v.size / tau
    mean = float(v.mean())
    se = float(v.std(ddof=1) / np.sqrt(n_eff))
    z = st.norm.ppf(0.975)
    return mean - z * se, mean + z * se


def missing_clock_bounds(z):
    z = np.asarray(z, float)
    hits = z[np.isfinite(z)]
    if hits.size < 3:
        return np.nan, np.nan
    return normal_ess_bounds(hits, geyer_tau_from_rho(pairwise_rho(z)))


def close_enough(cov_a, se_a, cov_b, se_b):
    gap = abs(cov_a - cov_b)
    tol = 2.0 * float(np.hypot(se_a, se_b))
    return bool(gap <= tol), gap, tol


def coverage_at(n, rng, kw):
    cells = {}
    tau_sub, tau_mis = [], []
    for _ in range(R):
        labels, scores = generate(2 * n, rng=rng, **kw)
        a_tr, s_tr = labels[:n], scores[:n]
        a_te, s_te = labels[n:], scores[n:]
        thr = np.quantile(s_tr[a_tr == 0], 1 - FPR) if (a_tr == 0).sum() >= 1 else np.nan
        truth = conditional_truth(thr, kw.get("mu", 2.0), kw.get("rho", 0.0), kw.get("H"))
        attack = a_te == 1
        hits = (s_te[attack] > thr).astype(float) if attack.any() else np.array([])
        z = np.full(a_te.size, np.nan)
        if attack.any():
            z[attack] = hits
        if hits.size >= 3:
            tau_sub.append(float(integrated_autocorrelation_time(hits, "geyer", guard=False)[0]))
            tau_mis.append(geyer_tau_from_rho(pairwise_rho(z)))
        _try(cells, "subsequence", lambda hits=hits: ess_plugin_ci(hits)[1:3], truth["recall"])
        _try(cells, "missing", lambda z=z: missing_clock_bounds(z), truth["recall"])
    rows = []
    for clock, (ncomp, ccov, ucov) in cells.items():
        cu = ucov / R
        cc = (ccov / ncomp) if ncomp else np.nan
        rows.append({
            "scenario": SCENARIO,
            "n": n,
            "clock": clock,
            "R": R,
            "cov_uncond": cu,
            "mc_se_uncond": _mc_se(cu, R),
            "cov_cond": cc,
            "mc_se_cond": _mc_se(cc, ncomp) if ncomp else np.nan,
            "comp_rate": ncomp / R,
            "n_computable": ncomp,
            "mean_tau": float(np.mean(tau_sub if clock == "subsequence" else tau_mis)) if (tau_sub if clock == "subsequence" else tau_mis) else np.nan,
        })
    return rows


def write_gate(path, cov):
    lines = [
        "# Week 3 gate — recall clock",
        "",
        "The claims use the attack-subsequence clock. The missing-clock arm treats benign",
        "rows as missing on the original test-set index. Closure is |coverage difference|",
        "<= 2 combined Monte Carlo standard errors, unconditional, at that sample size.",
        "",
    ]
    closed_all = True
    for n in SIZES:
        sub = cov[(cov.n == n) & (cov.clock == "subsequence")].iloc[0]
        mis = cov[(cov.n == n) & (cov.clock == "missing")].iloc[0]
        ok, gap, tol = close_enough(sub.cov_uncond, sub.mc_se_uncond, mis.cov_uncond, mis.mc_se_uncond)
        closed_all = closed_all and ok
        lines.append(
            f"- n={n}: subsequence {sub.cov_uncond:.3f} ± {sub.mc_se_uncond:.3f} "
            f"(tau {sub.mean_tau:.2f}), missing-clock {mis.cov_uncond:.3f} ± {mis.mc_se_uncond:.3f} "
            f"(tau {mis.mean_tau:.2f}), |gap| {gap:.3f}, tolerance {tol:.3f}, "
            f"{'closed' if ok else 'not closed'}."
        )
    lines += [
        "",
        "Objection closed at both sample sizes." if closed_all
        else "Objection not closed at every sample size. Both clocks are reported. The claims keep the subsequence.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")
    return closed_all


def main():
    kw = {k: v for k, v in SCENARIOS[SCENARIO].items() if k != "innov"}
    rng = np.random.default_rng(SEED)
    rows = []
    for n in SIZES:
        print(f"n={n}", flush=True)
        rows.extend(coverage_at(n, rng, kw))
    cov = pd.DataFrame(rows)
    out = ROOT / "results" / "recall_clock.csv"
    cov.to_csv(out, index=False)
    closed = write_gate(ROOT / "docs" / "week3_gate.md", cov)
    print(cov.to_string(index=False), flush=True)
    print("closed" if closed else "not closed", flush=True)


if __name__ == "__main__":
    main()
