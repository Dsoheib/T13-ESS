"""Coverage simulation on synthetic dependent telemetry.

Generative model (parameters preregistered):
  attack state a_t : two-state Markov chain (campaigns), p_stay = attack persistence
  background e_t   : AR(1) with coefficient rho, OR fractional Gaussian noise with Hurst H
                     (long-range dependence, the Paxson-Floyd regime)
  score s_t = mu * a_t + e_t ;  label y_t = a_t
Protocol mirrors a paper with a TIME-AWARE split: the first half is "training" and fixes
the operating threshold (quantile of training benign scores at the target FPR); the second
half is the test set on which intervals are computed. This is why a chronological split
does not repair the interval.
Truth = the metric on a very long realisation with the same threshold rule (population).
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy.signal import lfilter
from scipy.stats import norm
from . import ci as C
from .dif import integrated_autocorrelation_time


def conditional_truth(thr, mu, rho=0.0, H=None):
    """Exact metric values GIVEN the learned threshold: the estimand a test-set interval
    actually targets (it conditions on the operating point). Background marginal is
    N(0, 1/(1-rho^2)) for AR(1) and N(0,1) for fGn."""
    sd = 1.0 if H is not None or rho == 0 else 1.0 / np.sqrt(1 - rho ** 2)
    return {"fpr": float(1 - norm.cdf(thr / sd)), "recall": float(1 - norm.cdf((thr - mu) / sd))}


def fgn(n, H, rng):
    """Fractional Gaussian noise via Davies-Harte circulant embedding."""
    k = np.arange(0, n)
    gamma = 0.5 * (np.abs(k - 1) ** (2 * H) - 2 * np.abs(k) ** (2 * H) + np.abs(k + 1) ** (2 * H))
    row = np.concatenate([gamma, gamma[-2:0:-1]])
    lam = np.fft.fft(row).real
    lam = np.clip(lam, 0, None)
    m = row.size
    w = rng.normal(size=m) + 1j * rng.normal(size=m)
    x = np.fft.fft(np.sqrt(lam / (2 * m)) * w).real[:n] * np.sqrt(2)
    return x / x.std()


def markov_labels(n, p_stay, prevalence, rng):
    p01 = (1 - p_stay) * prevalence / (1 - prevalence); p10 = 1 - p_stay
    a = np.empty(0, dtype=int)
    k = max(8, int(4 * n * max(p01, p10)) + 8)
    while a.size < n:
        ben = rng.geometric(p01, k); att = rng.geometric(p10, k)
        runs = np.empty(2 * k, dtype=int); runs[0::2] = ben; runs[1::2] = att
        states = np.zeros(2 * k, dtype=int); states[1::2] = 1
        a = np.concatenate([a, np.repeat(states, runs)])
    off = rng.integers(0, max(1, a.size - n))
    return a[off:off + n]


def generate(n, rho=0.9, p_stay=0.995, prevalence=0.05, mu=2.0, H=None, innov="gauss", rng=None):
    """innov: 'gauss' or 't3' (Student-t, 3 d.f., scaled to unit variance) — heavy-tailed
    background to check that DIF and coverage do not depend on Gaussianity."""
    rng = np.random.default_rng(rng)
    a = markov_labels(n, p_stay, prevalence, rng)
    if H is not None:
        e = fgn(n, H, rng)
    else:
        z = rng.normal(0, 1, n) if innov == "gauss" else rng.standard_t(3, n) / np.sqrt(3.0)
        if rho != 0:
            z[0] = rng.normal(0, 1 / np.sqrt(1 - rho ** 2))
            e = lfilter([1.0], [1.0, -rho], z)
        else:
            e = z
    return a, mu * a + e


def population_truth(fpr, n_pop=400_000, **kw):
    a, s = generate(n_pop, rng=12345, **kw)
    thr = np.quantile(s[a == 0], 1 - fpr)
    return {"recall": float(np.mean(s[a == 1] > thr)), "auc": C.auc(a, s), "thr": thr,
            "acc": float(np.mean((s > thr) == a)), "fpr": float(np.mean(s[a == 0] > thr))}


def window_truth(n, fpr, R=400, min_pos=20, **kw):
    """Window-conditional truth: E[metric_hat | test window non-degenerate] under the same
    time-aware protocol. Separates interval WIDTH (our claim) from the selection effect of
    conditioning on windows that contain attacks. Both truths are reported."""
    rng = np.random.default_rng(777); acc = {"recall": [], "auc": [], "fpr": []}
    while min(len(v) for v in acc.values()) < R:
        a, s = generate(2 * n, rng=rng, **kw)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < min_pos or a_te.sum() < min_pos or (a_te == 0).sum() < min_pos:
            continue
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr)
        acc["recall"].append(np.mean(s_te[a_te == 1] > thr)); acc["fpr"].append(np.mean(s_te[a_te == 0] > thr))
        acc["auc"].append(C.auc(a_te, s_te))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def dif_estimator_study(taus=(3, 10, 30, 100), ns=(2000, 5000, 20000, 80000), R=40, seed=0):
    """Sampling error of each DIF rule vs n and true tau (AR(1): tau=(1+rho)/(1-rho)).
    The audit multiplies SEs by sqrt(DIF); this table says how much of that is estimation noise."""
    from .dif import integrated_autocorrelation_time, RULES
    rng = np.random.default_rng(seed); rows = []
    for tau in taus:
        rho = (tau - 1) / (tau + 1)
        for n in ns:
            est = {r: [] for r in RULES}
            for _ in range(R):
                z = rng.normal(0, 1, n); z[0] = rng.normal(0, 1 / np.sqrt(1 - rho ** 2))
                x = lfilter([1.0], [1.0, -rho], z)
                for r in RULES:
                    est[r].append(integrated_autocorrelation_time(x, r)[0])
            row = {"tau_true": tau, "n": n, "n_eff_true": n / tau}
            for r in RULES:
                e = np.array(est[r]); row[f"relbias_{r}"] = e.mean() / tau - 1; row[f"relsd_{r}"] = e.std() / tau
            rows.append(row)
    return pd.DataFrame(rows)


# ---- scenarios: a 2x2 factorial of the two dependence SOURCES, plus lrd and heavy tail ----
# background {iid, AR(1)} x labels {scattered, campaign}. Old names kept as aliases so
# existing diagnostics/tests keep working.
_BG_IID_SCAT = dict(rho=0.0, p_stay=0.05,  prevalence=0.05, mu=2.0)   # control
_BG_IID_CAMP = dict(rho=0.0, p_stay=0.995, prevalence=0.05, mu=2.0)   # campaigns only
_BG_AR_SCAT  = dict(rho=0.9, p_stay=0.05,  prevalence=0.05, mu=2.0)   # background only
_BG_AR_CAMP  = dict(rho=0.9, p_stay=0.995, prevalence=0.05, mu=2.0)   # both
SCENARIOS = {
    "bg_iid__lab_scatter":  _BG_IID_SCAT, "iid":            _BG_IID_SCAT,
    "bg_iid__lab_campaign": _BG_IID_CAMP, "campaigns_only": _BG_IID_CAMP,
    "bg_ar__lab_scatter":   _BG_AR_SCAT,  "background_only": _BG_AR_SCAT,
    "bg_ar__lab_campaign":  _BG_AR_CAMP,  "dependent":      _BG_AR_CAMP,
    "lrd_H0.8":   dict(rho=0.0, p_stay=0.995, prevalence=0.05, mu=2.0, H=0.8),
    "heavy_tail": dict(rho=0.9, p_stay=0.995, prevalence=0.05, mu=2.0, innov="t3"),
}
FACTORIAL = ["bg_iid__lab_scatter", "bg_iid__lab_campaign", "bg_ar__lab_scatter", "bg_ar__lab_campaign"]


def _mc_se(p, n):
    return float(np.sqrt(p * (1 - p) / n)) if n > 0 else np.nan


def _record(cells, key, computable, covered):
    """cells[key] accumulates (n_computable, n_covered_computable, n_covered_uncond)."""
    c = cells.setdefault(key, [0, 0, 0])
    if computable:
        c[0] += 1
        if covered:
            c[1] += 1; c[2] += 1
    # non-computable -> counts as a miss in the unconditional tally (c[2] unchanged)


def _try(cells, key, interval_fn, truth):
    """Compute an interval and record coverage. 'Computable' == the routine returned a finite
    [lo, hi]; any failure (too few samples for the ACF, empty class, NaN) is a non-computable
    rep, which the unconditional tally counts as a miss (P9)."""
    try:
        lo, hi = interval_fn()
        if lo is None or hi is None or np.isnan(lo) or np.isnan(hi):
            _record(cells, key, False, False)
        else:
            _record(cells, key, True, lo <= truth <= hi)
    except Exception:
        _record(cells, key, False, False)


def coverage_run(name, kw, n=5000, R=500, B=200, fpr=0.01, seed=0, split="temporal",
                 include_episode=True):
    """Single canonical coverage experiment (replaces one_replication/floor_curve path).

    Estimand: threshold-conditional truth for FPR/recall (the charitable estimand -- the metric
    at the realised learned threshold); population for AUC (threshold-free).
    Reporting (P9): for each (metric, interval) two coverages are returned --
      cov_uncond   : non-computable intervals COUNT AS FAILURES (headline);
      cov_cond     : coverage among computable reps only;
      comp_rate    : fraction of the R reps in which the interval was computable.
    An interval is non-computable when its class is too small to form it: FPR needs >=1 benign,
    recall (normal/ESS) needs >=2 attack, AUC needs >=1 of each.
    """
    pop = population_truth(fpr, **kw)
    rng = np.random.default_rng(seed)
    cells = {}; difs = []; neffs = []; natt_list = []
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        if split == "random":
            perm = rng.permutation(2 * n); a, s = a[perm], s[perm]
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        # threshold from training benign; if training has no benign, fall back to population thr
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr) if (a_tr == 0).sum() >= 1 else pop["thr"]
        cond = conditional_truth(thr, kw.get("mu", 2.0), kw.get("rho", 0.0), kw.get("H"))
        nben = int((a_te == 0).sum()); natt = int((a_te == 1).sum()); natt_list.append(natt)
        try:
            tau_s, _ = integrated_autocorrelation_time(s_te, "geyer"); difs.append(tau_s); neffs.append(n / tau_s)
        except Exception:
            pass
        alarms = (s_te[a_te == 0] > thr).astype(float) if nben >= 1 else np.array([])
        hits = (s_te[a_te == 1] > thr).astype(float) if natt >= 1 else np.array([])
        rat = C.recall_at_threshold(thr); fpt = C.fpr_at_threshold(thr)
        # ---- FPR (threshold-conditional) ----
        _try(cells, "fpr|naiveWilson", lambda: C.wilson(alarms.sum(), alarms.size)[1:], cond["fpr"])
        _try(cells, "fpr|corrWilson", lambda: C.wilson_ess_ci(alarms)[1:3], cond["fpr"])
        _try(cells, "fpr|mbb", lambda: C.block_bootstrap_ci(a_te, s_te, fpt, B=B, rng=rng, kind="basic")[1:3], cond["fpr"])
        # ---- recall (threshold-conditional) ----
        _try(cells, "recall|naiveNormal", lambda: C.naive_normal_ci(hits)[1:], cond["recall"])
        _try(cells, "recall|ess", lambda: C.ess_plugin_ci(hits)[1:3], cond["recall"])
        _try(cells, "recall|mbb", lambda: C.block_bootstrap_ci(a_te, s_te, rat, B=B, rng=rng, kind="basic")[1:3], cond["recall"])
        if include_episode:   # O(episodes*B); skip for large-n confirmation (behaviour set by episode count, see p13)
            _try(cells, "recall|episode", lambda: C.episode_bootstrap_ci(a_te, s_te, rat, B=B, rng=rng, kind="basic")[1:3], cond["recall"])
        # ---- AUC (threshold-free -> population truth) ----
        _try(cells, "auc|naiveBoot", lambda: C.naive_iid_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng)[1:], pop["auc"])
        _try(cells, "auc|mbb", lambda: C.block_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng, kind="basic")[1:3], pop["auc"])
        _try(cells, "auc|bjk", lambda: C.block_jackknife_auc(a_te, s_te)[1:3], pop["auc"])
    rows = []
    for key, (ncomp, ccov, ucov) in cells.items():
        metric, interval = key.split("|")
        cu = ucov / R; cc = (ccov / ncomp) if ncomp else np.nan
        rows.append({"scenario": name, "split": split, "metric": metric, "interval": interval,
                     "cov_uncond": round(cu, 3), "mc_se_uncond": round(_mc_se(cu, R), 3),
                     "cov_cond": round(cc, 3) if ncomp else np.nan,
                     "mc_se_cond": round(_mc_se(cc, ncomp), 3) if ncomp else np.nan,
                     "comp_rate": round(ncomp / R, 3), "R": R, "n_computable": ncomp})
    meta = {"scenario": name, "split": split, "mean_dif_score": round(float(np.mean(difs)), 1),
            "mean_neff_score": round(float(np.mean(neffs)), 1), "mean_n_attack_test": round(float(np.mean(natt_list)), 1),
            **{k: kw.get(k) for k in ("rho", "p_stay", "H", "innov")}}
    return pd.DataFrame(rows), meta


def run(scenarios=None, n=5000, R=500, B=200, fpr=0.01, seed=0, split="temporal"):
    """Driver: canonical dual-reported coverage over a set of scenarios (long format)."""
    names = scenarios or list(dict.fromkeys(FACTORIAL + ["lrd_H0.8", "heavy_tail"]))
    frames, metas = [], []
    for name in names:
        df, meta = coverage_run(name, SCENARIOS[name], n=n, R=R, B=B, fpr=fpr, seed=seed, split=split)
        frames.append(df); metas.append(meta)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(metas)
