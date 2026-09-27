"""Dependence-inflation factor (DIF) and effective sample size (ESS).

n_eff = n / tau_int,  tau_int = 1 + 2 * sum_{k>=1} rho_k ;  DIF = n / n_eff = tau_int.

Truncation / estimation rules (prereg fixes one as primary):
  geyer    : initial positive sequence (Geyer 1992)             [primary]
  batch    : batch-means ESS (Flegal & Jones 2010), b = n**(1/2)  [robustness, LRD-tolerant]
  ar1      : AR(1) plug-in tau = (1+rho1)/(1-rho1)               [interpretable lower bound]
  zero     : first non-positive autocorrelation
  bartlett : Bartlett window M = n**(1/3)  (biased low under strong dependence; sensitivity only)

Reliability flags: an estimate is UNRELIABLE when lag_used > n/20 (too few effective
epochs) or n_eff < 50. Under long-range dependence (fGn with H > 0.5) tau_int diverges and
DIF grows with n; report DIF at the analysed n and the batch-means estimate, and say so.
"""
from __future__ import annotations
import numpy as np

RULES = ("geyer", "batch", "ar1", "zero", "bartlett")


def acf(x, max_lag=None):
    x = np.asarray(x, dtype=float); n = x.size
    if n < 3:
        raise ValueError("need at least 3 observations")
    x = x - x.mean(); var = np.dot(x, x) / n
    if max_lag is None:
        max_lag = n - 1
    if var == 0.0:
        out = np.zeros(max_lag + 1); out[0] = 1.0; return out
    nfft = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, nfft)
    ac = np.fft.irfft(f * np.conj(f), nfft)[:n] / n
    return (ac / var)[: max_lag + 1]


def _batch_means_tau(x, b=None):
    x = np.asarray(x, float); n = x.size
    if b is None:
        b = max(2, int(np.floor(np.sqrt(n))))
    a = n // b
    if a < 2:
        return np.nan
    means = x[: a * b].reshape(a, b).mean(axis=1)
    var_batch = means.var(ddof=1)
    var_x = x.var(ddof=1)
    if var_x == 0:
        return 1.0
    return max(1.0, b * var_batch / var_x)


class EstimatorFloorError(ValueError):
    """Geyer floored at tau=1.0 while batch-means reports strong dependence: the series is
    almost certainly not in true temporal order (shuffled / non-monotone timestamps / heavy
    duplication) or non-stationary. Reporting DIF=1.0 here would be a bug, not a finding."""


def integrated_autocorrelation_time(x, rule="geyer", max_lag=None, guard=True):
    """Return (tau_int, lag_used); tau_int clipped at >= 1.

    guard=True (default): if the Geyer estimator floors at exactly tau=1.0 (rho_1 <= 0) while
    the batch-means estimator on the same series exceeds 5, raise EstimatorFloorError instead of
    silently returning 1.0 (P22). Batch is computed only in the floored case, so dependent
    series pay no cost."""
    x = np.asarray(x, dtype=float); n = x.size
    if rule == "batch":
        return _batch_means_tau(x), int(np.sqrt(n))
    if max_lag is None:
        max_lag = min(n - 2, max(50, int(20 * n ** 0.5)))
    rho = acf(x, max_lag)
    if rule == "ar1":
        r1 = float(np.clip(rho[1], -0.999, 0.999))
        return max(1.0, (1 + r1) / (1 - r1)), 1
    if rule == "zero":
        k, s = 1, 0.0
        while k <= max_lag and rho[k] > 0:
            s += rho[k]; k += 1
        return max(1.0, 1.0 + 2.0 * s), k - 1
    if rule == "bartlett":
        M = min(max(1, int(np.floor(n ** (1.0 / 3.0)))), max_lag)
        w = 1.0 - np.arange(1, M + 1) / (M + 1.0)
        return max(1.0, 1.0 + 2.0 * float(np.sum(w * rho[1:M + 1]))), M
    if rule == "geyer":
        s, m, lag_used = 0.0, 0, 0
        while True:
            i, j = 2 * m, 2 * m + 1
            if j > max_lag:
                break
            g = rho[i] + rho[j]
            if g <= 0:
                break
            s += g; lag_used = j; m += 1
        tau_g = max(1.0, -1.0 + 2.0 * s)
        if guard and tau_g <= 1.0 + 1e-9:
            tb = _batch_means_tau(x)
            if tb == tb and tb > 5:   # tb not NaN and > 5
                raise EstimatorFloorError(
                    f"Geyer floored at tau=1.0 but batch-means tau={tb:.1f}>5; series likely "
                    f"not in temporal order or non-stationary (n={n})")
        return tau_g, lag_used
    raise ValueError(f"unknown rule {rule!r}; choose from {RULES}")


def ess(x, rule="geyer"):
    tau, _ = integrated_autocorrelation_time(x, rule)
    return float(np.asarray(x).size / tau)


def dif(x, rule="geyer"):
    tau, _ = integrated_autocorrelation_time(x, rule)
    return float(tau)


def reliability(x, rule="geyer"):
    x = np.asarray(x); n = x.size
    tau, lag = integrated_autocorrelation_time(x, rule)
    flags = []
    if lag > n / 20:
        flags.append("lag_used>n/20")
    if n / tau < 50:
        flags.append("n_eff<50")
    return {"tau": tau, "lag_used": lag, "n_eff": n / tau, "reliable": not flags, "flags": flags}


def block_length(*series, rule="geyer", multiplier=2.0, min_len=2):
    """Block length = multiplier * tau_int of the SLOWEST of the given series
    (labels, scores, ...), floored at min_len and capped at n**(2/3)."""
    taus = []; n = None
    for s in series:
        s = np.asarray(s, float); n = s.size if n is None else min(n, s.size)
        taus.append(integrated_autocorrelation_time(s, rule)[0])
    L = int(np.ceil(multiplier * max(taus)))
    cap = max(min_len, int(n ** (2.0 / 3.0)))
    return int(min(max(min_len, L), cap))


def politis_white_block_length(x, kn=None):
    """Politis & White (2004) automatic block length with the Patton et al. (2009)
    correction, flat-top lag window. Returns (L_mbb, L_sb) for moving-block and
    stationary bootstrap. Standard in econometrics; used as the prereg alternative to
    2*tau_int so a referee cannot ask 'why not Politis-White'."""
    x = np.asarray(x, float); n = x.size
    if kn is None:
        kn = max(5, int(np.log10(n)))
    m_max = int(np.ceil(np.sqrt(n))) + kn
    rho = acf(x, m_max)
    # first m such that kn consecutive |rho| below 2*sqrt(log10(n)/n)
    thresh = 2 * np.sqrt(np.log10(n) / n)
    m_hat = None
    for m in range(1, m_max - kn + 1):
        if np.all(np.abs(rho[m:m + kn]) < thresh):
            m_hat = m; break
    if m_hat is None:
        m_hat = m_max - kn
    M = min(2 * m_hat, m_max)
    k = np.arange(-M, M + 1)
    lam = np.where(np.abs(k) <= M / 2, 1.0, 2.0 * (1 - np.abs(k) / M))
    lam = np.clip(lam, 0, 1)
    R = np.array([rho[abs(j)] for j in k]) * x.var()
    G = float(np.sum(lam * np.abs(k) * R))
    D_sb = 2 * float(np.sum(lam * R)) ** 2
    D_mbb = (4.0 / 3.0) * float(np.sum(lam * R)) ** 2
    if D_sb <= 0 or G == 0:
        return 2, 2
    L_sb = (2 * G ** 2 / D_sb) ** (1 / 3) * n ** (1 / 3)
    L_mbb = (2 * G ** 2 / D_mbb) ** (1 / 3) * n ** (1 / 3)
    cap = int(np.ceil(min(3 * np.sqrt(n), n / 3)))
    return int(min(max(2, round(L_mbb)), cap)), int(min(max(2, round(L_sb)), cap))


def n_blocks(n, L):
    return int(np.ceil(n / L))


def dif_ci(x, rule="geyer", K=8, alpha=0.05, rng=None):
    """Interval for DIF itself by contiguous segmentation: the series is cut into K equal
    contiguous segments, tau is estimated on each, and a t-interval is formed across segments.
    (A block bootstrap of tau is biased low because block edges break correlation; a
    segment-based interval keeps every within-segment dependence intact.) Requires each
    segment to hold >= 20 tau; otherwise the interval is flagged unreliable.
    Returns (tau_full, lo, hi, reliable)."""
    from scipy import stats as _st
    x = np.asarray(x, float); n = x.size
    tau0, _ = integrated_autocorrelation_time(x, rule)
    seg = n // K
    taus = np.array([integrated_autocorrelation_time(x[i * seg:(i + 1) * seg], rule)[0] for i in range(K)])
    m = taus.mean(); se = taus.std(ddof=1) / np.sqrt(K)
    h = _st.t.ppf(1 - alpha / 2, K - 1) * se
    reliable = seg >= 20 * tau0
    return tau0, max(1.0, m - h), m + h, bool(reliable)


def agreement(x, tol=2.0):
    """Geyer vs batch-means DIF must agree within a factor tol, else the series is flagged
    (typical cause: long-range dependence or n too short for the dependence scale)."""
    g = integrated_autocorrelation_time(x, "geyer")[0]; b = integrated_autocorrelation_time(x, "batch")[0]
    r = max(g, b) / max(1e-12, min(g, b))
    return {"ratio_geyer_batch": r, "agree": r <= tol}


def dif_report(x):
    out = {"n": int(np.asarray(x).size)}
    for r in RULES:
        tau, lag = integrated_autocorrelation_time(x, r)
        out[f"dif_{r}"] = tau; out[f"lag_{r}"] = lag; out[f"n_eff_{r}"] = out["n"] / tau
    out.update({f"rel_{k}": v for k, v in reliability(x).items() if k in ("reliable", "flags")})
    out.update(agreement(x))
    return out
