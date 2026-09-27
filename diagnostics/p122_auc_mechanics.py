"""Hostile audit of the AUC interval: is the shortfall a width failure, a bootstrap failure, or a
property of the chosen target?

The moving-block interval is scored against a long-run Monte Carlo reference theta_ref. Three
distinct things can push coverage below nominal, and coverage alone cannot tell them apart:

  1. target offset   E[AUC_n] != theta_ref. The reference is the stationary pairwise functional,
                     which is deliberately not the finite-n expectation, so any gap is an estimand
                     choice that coverage pays for.
  2. width failure   the interval is narrower than the sampling variability of AUC_n.
  3. bootstrap law   the moving-block distribution of (theta* - theta_hat) does not match the
                     sampling distribution of (theta_hat - theta). This is the validity criterion
                     for the bootstrap, and it is what the basic interval relies on.

For each cell we report all three, plus the coverage that would be observed if the target were
recentred on E[AUC_n]. The difference between the two coverages is the part attributable to the
reference definition rather than to the interval.
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, population_truth, SCENARIOS
from t13.dif import block_length
from t13 import ci as C

CELLS = {"both": SCENARIOS["bg_ar__lab_campaign"],
         "campaigns only": SCENARIOS["bg_iid__lab_campaign"],
         "iid (control)": SCENARIOS["bg_iid__lab_scatter"]}


def run(kw, n, R=300, B=200, seed=0):
    ref = float(population_truth(0.01, **kw)["auc"])
    rng = np.random.default_rng(seed)
    est, boot_sd, boot_bias, lo_hi, Ls = [], [], [], [], []
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        a_te, s_te = a[n:], s[n:]
        if a_te.sum() < 2 or (a_te == 0).sum() < 2:
            continue
        theta = C.auc(a_te, s_te)
        if theta != theta:
            continue
        L = block_length(a_te.astype(float), s_te)
        boots = np.empty(B)
        for b in range(B):
            idx = C._mbb_indices(n, L, rng)
            boots[b] = C.auc(a_te[idx], s_te[idx])
        good = boots[~np.isnan(boots)]
        if good.size < 10:
            continue
        q_lo, q_hi = np.percentile(good, [2.5, 97.5])
        est.append(theta); Ls.append(L)
        boot_sd.append(good.std(ddof=1))
        boot_bias.append(good.mean() - theta)
        lo_hi.append((2 * theta - q_hi, 2 * theta - q_lo))
    est = np.array(est); lo_hi = np.array(lo_hi)
    boot_sd = np.array(boot_sd); boot_bias = np.array(boot_bias)
    sd_true = est.std(ddof=1)
    mean_est = est.mean()
    cov_ref = float(np.mean((lo_hi[:, 0] <= ref) & (ref <= lo_hi[:, 1])))
    cov_rec = float(np.mean((lo_hi[:, 0] <= mean_est) & (mean_est <= lo_hi[:, 1])))
    return {"n": n, "reps": est.size, "mean_L": round(float(np.mean(Ls)), 1),
            "theta_ref": round(ref, 4), "mean_auc_n": round(float(mean_est), 4),
            "target_offset": round(float(mean_est - ref), 4),
            "sd_auc_n": round(float(sd_true), 4),
            "offset_in_sd": round(float((mean_est - ref) / sd_true), 2),
            "mean_boot_sd": round(float(boot_sd.mean()), 4),
            "boot_sd_ratio": round(float(boot_sd.mean() / sd_true), 3),
            "mean_boot_bias": round(float(boot_bias.mean()), 4),
            "cov_vs_reference": round(cov_ref, 3),
            "cov_vs_mean_auc_n": round(cov_rec, 3),
            "cov_gap_from_target": round(cov_rec - cov_ref, 3)}


rows = []
for cell, kw in CELLS.items():
    for n in (5000, 20000):
        r = run(kw, n)
        r["cell"] = cell
        rows.append(r)
        print({k: r[k] for k in ("cell", "n", "theta_ref", "mean_auc_n", "offset_in_sd",
                                 "boot_sd_ratio", "cov_vs_reference", "cov_vs_mean_auc_n")},
              flush=True)
df = pd.DataFrame(rows)[["cell", "n", "reps", "mean_L", "theta_ref", "mean_auc_n",
                         "target_offset", "sd_auc_n", "offset_in_sd", "mean_boot_sd",
                         "boot_sd_ratio", "mean_boot_bias", "cov_vs_reference",
                         "cov_vs_mean_auc_n", "cov_gap_from_target"]]
df.to_csv("diagnostics/p122_auc.csv", index=False)
pd.set_option("display.width", 250)
print("\n" + df.to_string(index=False))
print("\nwrote diagnostics/p122_auc.csv")
