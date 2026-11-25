"""Coverage of the paired AUC-difference interval.

The manuscript's motivating use case is choosing between detectors, and its real-data ranking
result (S4.7) is adjudicated by `ci.paired_difference_ci`. The coverage simulation scores the
single-detector FPR, recall and AUC intervals; it never scored the paired difference. This does.

Design. Two detectors observe the SAME traffic: one label chain and one background series shared
between them, plus independent detector-specific noise, and different separations mu_A and mu_B.
That is the situation the manuscript's Wednesday comparison is in -- two models scored on one
capture -- and it is the reason the result differs from the single-AUC case: the shared background
largely cancels in a difference, while the shared label clustering does not.

The estimand is the difference in the stationary pairwise AUC functional, taken from one long
reference draw, the same device the coverage simulation uses for the single-AUC target. Both arms
use the basic bootstrap interval, matching `scripts/metric_level_intervals.py`, so the moving-block
column is the construction that produces the reported ranking result.

Additive: the frozen generator is called through `t13.sim.generate`; nothing in it is modified.
Writes diagnostics/paired_difference.csv.
"""
import sys, argparse, time
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
import t13.sim as S
import t13.ci as C

# One modest, genuine gap between two detectors, and the detector-specific noise that makes them
# two models rather than one model twice.
MU_A, MU_B, SIGMA_D = 2.0, 1.8, 0.5
REFERENCE_N, REFERENCE_SEED = 400_000, 12345

CELLS = {
    "iid (control)":   dict(rho=0.0, p_stay=0.05,  prevalence=0.05),
    "campaigns only":  dict(rho=0.0, p_stay=0.995, prevalence=0.05),
    "background only": dict(rho=0.9, p_stay=0.05,  prevalence=0.05),
    "both":            dict(rho=0.9, p_stay=0.995, prevalence=0.05),
}


def generate_pair(n, rng, rho, p_stay, prevalence, mu_a=MU_A, mu_b=MU_B, sigma_d=SIGMA_D):
    """One label chain and one background, shared by two detectors."""
    labels, background = S.generate(n, rng=rng, rho=rho, p_stay=p_stay,
                                    prevalence=prevalence, mu=0.0)
    score_a = mu_a * labels + background + sigma_d * rng.normal(size=n)
    score_b = mu_b * labels + background + sigma_d * rng.normal(size=n)
    return labels, score_a, score_b


def reference_difference(cell_kwargs):
    """Long-run Monte Carlo reference for the true AUC difference."""
    rng = np.random.default_rng(REFERENCE_SEED)
    y, sa, sb = generate_pair(REFERENCE_N, rng, **cell_kwargs)
    return float(C.auc(y, sa) - C.auc(y, sb))


def iid_paired_ci(y, sa, sb, B, rng, alpha=0.05):
    """Ordinary bootstrap of the rows, basic interval -- the comparator arm."""
    n = y.size
    d0 = C.auc(y, sa) - C.auc(y, sb)
    boots = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n)
        boots[b] = C.auc(y[idx], sa[idx]) - C.auc(y[idx], sb[idx])
    lo_q, hi_q = np.nanquantile(boots, [alpha / 2, 1 - alpha / 2])
    return d0, 2 * d0 - hi_q, 2 * d0 - lo_q


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=5000)
    p.add_argument("--R", type=int, default=300)
    p.add_argument("--B", type=int, default=200)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()

    rows = []
    for name, kw in CELLS.items():
        truth = reference_difference(kw)
        rng = np.random.default_rng(a.seed)
        hit = {"iid bootstrap": 0, "moving block": 0}
        width = {"iid bootstrap": [], "moving block": []}
        t0 = time.time()
        for _ in range(a.R):
            y, sa, sb = generate_pair(a.n, rng, **kw)
            if y.sum() < 2 or (1 - y).sum() < 2:
                continue
            d_m, mlo, mhi, _L, _nb, _pv, _ok = C.paired_difference_ci(
                y, sa, sb, C.auc, B=a.B, rng=rng, kind="basic")
            _d_i, ilo, ihi = iid_paired_ci(y, sa, sb, a.B, rng)
            for label, (lo, hi) in (("moving block", (mlo, mhi)), ("iid bootstrap", (ilo, ihi))):
                if np.isfinite(lo) and np.isfinite(hi):
                    width[label].append(hi - lo)
                    if lo <= truth <= hi:
                        hit[label] += 1
        for label in ("iid bootstrap", "moving block"):
            c = hit[label] / a.R
            rows.append({"cell": name, "n": a.n, "interval": label,
                         "truth_auc_diff": round(truth, 4),
                         "cov_uncond": round(c, 3),
                         "mc_se_uncond": round(float(np.sqrt(c * (1 - c) / a.R)), 3),
                         "mean_width": round(float(np.mean(width[label])), 4),
                         "R": a.R, "B": a.B})
        print(f"{name:16s} truth {truth:+.4f}  "
              f"iid {hit['iid bootstrap']/a.R:.3f}  mbb {hit['moving block']/a.R:.3f}  "
              f"({time.time()-t0:.0f}s)", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("diagnostics/paired_difference.csv", index=False)
    print(out.to_string(index=False))
