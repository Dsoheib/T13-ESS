"""Coverage of the moving-block AUC interval as the block-length multiplier varies.

Eq. (L) fixes the multiplier at 2. That rule is prespecified, and the paper evaluates it
without comparing it to any other multiplier. This script runs the same coverage experiment
as coverage_run (same generator, split, threshold, statistic, B and seed) with the multiplier
set to 1, 2 and 4, so the multiplier-2 arm reproduces the reported cell and the other two say
how much the reported coverage depends on that choice.

Output: results/block_length_sensitivity.csv
"""
import sys, argparse
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, population_truth, SCENARIOS
from t13.dif import block_length
from t13 import ci as C

CELLS = [("bg_ar__lab_campaign", "both"), ("bg_iid__lab_campaign", "campaigns only")]
MULTIPLIERS = (1.0, 2.0, 4.0)


def _mc_se(p, n):
    return float(np.sqrt(p * (1 - p) / n)) if n > 0 else np.nan


def run(n=5000, R=500, B=200, fpr=0.01, seed=0):
    rows = []
    for scen, label in CELLS:
        kw = SCENARIOS[scen]
        pop = population_truth(fpr, **kw)
        rng = np.random.default_rng(seed)
        tally = {m: [0, 0, 0] for m in MULTIPLIERS}   # n_computable, covered_comp, covered_uncond
        Ls = {m: [] for m in MULTIPLIERS}
        for _ in range(R):
            a, s = generate(2 * n, rng=rng, **kw)
            a_te, s_te = a[n:], s[n:]
            for m in MULTIPLIERS:
                try:
                    L = block_length(a_te.astype(float), s_te, multiplier=m)
                    _, lo, hi, *_ = C.block_bootstrap_ci(a_te, s_te, C.auc, L=L, B=B,
                                                         rng=rng, kind="basic")
                    Ls[m].append(L)
                    if lo is None or hi is None or np.isnan(lo) or np.isnan(hi):
                        continue
                    tally[m][0] += 1
                    if lo <= pop["auc"] <= hi:
                        tally[m][1] += 1; tally[m][2] += 1
                except Exception:
                    pass
        for m in MULTIPLIERS:
            ncomp, ccov, ucov = tally[m]
            cu = ucov / R; cc = (ccov / ncomp) if ncomp else np.nan
            rows.append({"scenario": scen, "label": label, "multiplier": m,
                         "mean_L": round(float(np.mean(Ls[m])), 1) if Ls[m] else np.nan,
                         "cov_uncond": round(cu, 3), "mc_se_uncond": round(_mc_se(cu, R), 3),
                         "cov_cond": round(cc, 3) if ncomp else np.nan,
                         "mc_se_cond": round(_mc_se(cc, ncomp), 3) if ncomp else np.nan,
                         "comp_rate": round(ncomp / R, 3), "n": n, "R": R, "B": B,
                         "seed": seed, "auc_reference": round(float(pop["auc"]), 4)})
            print(rows[-1], flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000); ap.add_argument("--R", type=int, default=500)
    ap.add_argument("--B", type=int, default=200); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    df = run(a.n, a.R, a.B, seed=a.seed)
    df.to_csv("results/block_length_sensitivity.csv", index=False)
    print(df.to_string(index=False))
    print("wrote results/block_length_sensitivity.csv")
