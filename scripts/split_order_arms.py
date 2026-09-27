"""FPR coverage under three orderings of the same dependent generator.

The published random-split arm permutes the series and hands the shuffled test
sequence to the interval. This script adds the missing arm: the same random
partition, with the test indices sorted back into original time before the
interval is built. Wilson intervals contain no bootstrap.

Arms
  temporal : first half train, second half test, acquisition order
  shuffled : permute, then split; the estimator sees the shuffled test order
  restored : same random partition as a paired shuffled draw, test indices
             sorted back into original time

Estimand: threshold-conditional FPR (same as coverage_run). Scenario matches
Table 2: bg_ar__lab_campaign. Output: results/split_order_arms.csv.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from t13.sim import generate, population_truth, conditional_truth, SCENARIOS
from t13 import ci as C
from t13.dif import integrated_autocorrelation_time as tau


def _wilson_pair(alarms, truth):
    """Return (naive_hit, ess_hit) or None for a non-computable interval."""
    if alarms.size < 1:
        return None, None
    try:
        _, lo, hi = C.wilson(alarms.sum(), alarms.size)
        naive = bool(lo <= truth <= hi)
    except Exception:
        naive = None
    try:
        _, lo, hi, _ = C.wilson_ess_ci(alarms)
        ess = bool(lo <= truth <= hi)
    except Exception:
        ess = None
    return naive, ess


def _split_views(a, s, n, rng):
    """One random partition: shuffled test order and time-restored test order."""
    perm = rng.permutation(2 * n)
    tr = perm[:n]
    te = perm[n:]
    shuffled = (a[perm][n:], s[perm][n:], a[tr], s[tr])
    order = np.sort(te)
    restored = (a[order], s[order], a[tr], s[tr])
    return shuffled, restored, te


def _alarms_and_tau(a_te, s_te, a_tr, s_tr, thr_fallback, fpr, mu, rho):
    if (a_tr == 0).sum() >= 1:
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr)
    else:
        thr = thr_fallback
    truth = conditional_truth(thr, mu, rho, None)["fpr"]
    benign = a_te == 0
    alarms = (s_te[benign] > thr).astype(float) if benign.any() else np.array([])
    scores = s_te[benign]
    t = np.nan
    if scores.size >= 3:
        t = float(tau(scores, "geyer", guard=False)[0])
    return alarms, truth, t


def run(n=20000, R=500, fpr=0.01, seed=1):
    kw = SCENARIOS["bg_ar__lab_campaign"]
    mu, rho = kw["mu"], kw["rho"]
    pop = population_truth(fpr, **kw)
    rng = np.random.default_rng(seed)
    hits = {k: {"naive": [], "ess": []} for k in ("temporal", "shuffled", "restored")}
    taus = {"temporal_seen": [], "shuffled_seen": [], "shuffled_true": []}
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        alarms, truth, t = _alarms_and_tau(a[n:], s[n:], a[:n], s[:n], pop["thr"], fpr, mu, rho)
        nv, es = _wilson_pair(alarms, truth)
        hits["temporal"]["naive"].append(nv)
        hits["temporal"]["ess"].append(es)
        if t == t:
            taus["temporal_seen"].append(t)

        a, s = generate(2 * n, rng=rng, **kw)
        (a_sh, s_sh, a_tr, s_tr), (a_re, s_re, _, _), te = _split_views(a, s, n, rng)
        alarms, truth, t_seen = _alarms_and_tau(a_sh, s_sh, a_tr, s_tr, pop["thr"], fpr, mu, rho)
        nv, es = _wilson_pair(alarms, truth)
        hits["shuffled"]["naive"].append(nv)
        hits["shuffled"]["ess"].append(es)
        alarms, truth, t_true = _alarms_and_tau(a_re, s_re, a_tr, s_tr, pop["thr"], fpr, mu, rho)
        nv, es = _wilson_pair(alarms, truth)
        hits["restored"]["naive"].append(nv)
        hits["restored"]["ess"].append(es)
        if t_seen == t_seen:
            taus["shuffled_seen"].append(t_seen)
        if t_true == t_true:
            taus["shuffled_true"].append(t_true)
    rows = []
    for arm in ("temporal", "shuffled", "restored"):
        for kind, key in (("naiveWilson", "naive"), ("essWilson", "ess")):
            v = np.array([x for x in hits[arm][key] if x is not None], dtype=float)
            # non-computable counts as a miss in the unconditional rate
            raw = np.array([0.0 if x is None else float(x) for x in hits[arm][key]])
            p = float(raw.mean())
            se = float(np.sqrt(p * (1 - p) / raw.size))
            pc = float(v.mean()) if v.size else np.nan
            rows.append({
                "arm": arm, "interval": kind, "n": n, "R": R, "seed": seed,
                "cov_uncond": round(p, 3), "mc_se_uncond": round(se, 3),
                "cov_cond": round(pc, 3) if v.size else np.nan,
                "comp_rate": round(v.size / raw.size, 3),
            })
    meta = {
        "tau_temporal_seen": round(float(np.mean(taus["temporal_seen"])), 2),
        "tau_shuffled_seen": round(float(np.mean(taus["shuffled_seen"])), 2),
        "tau_shuffled_true": round(float(np.mean(taus["shuffled_true"])), 2),
        "n": n, "R": R, "seed": seed,
    }
    return pd.DataFrame(rows), meta


if __name__ == "__main__":
    df, meta = run()
    df.to_csv("results/split_order_arms.csv", index=False)
    pd.DataFrame([meta]).to_csv("results/split_order_arms_meta.csv", index=False)
    print(df.to_string(index=False))
    print(meta)
