"""Does each plug-in deliver the right width for the estimand it targets?

The coverage target is the threshold-conditional metric, which moves with the realised threshold.
So the yardstick is the spread of (estimate - conditional truth), not the spread of the estimate.
This separates two failures that coverage alone conflates:
  variance failure : reported se is smaller than sd(estimate - target)
  shape failure    : se is right but the normal/Wilson shape is wrong in the tail.

Also reports the implied number of independent units, to compare the plug-in's n_eff against the
sample size the observed variability actually corresponds to.
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from scipy import stats as st
from t13.sim import generate, conditional_truth, SCENARIOS
from t13 import ci as C

FPR, Z = 0.01, st.norm.ppf(0.975)
CELLS = {"both": SCENARIOS["bg_ar__lab_campaign"], "campaigns only": SCENARIOS["bg_iid__lab_campaign"]}


def run(kw, n, R=400, seed=23):
    rng = np.random.default_rng(seed)
    out = {k: [] for k in ("f_err", "f_ess_se", "f_naive_se", "f_neff", "f_nben",
                           "r_err", "r_ess_se", "r_naive_se", "r_neff", "r_natt", "r_ncamp")}
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < 30 or (a_te == 0).sum() < 30 or a_te.sum() < 30:
            continue
        thr = float(np.quantile(s_tr[a_tr == 0], 1 - FPR))
        cond = conditional_truth(thr, kw.get("mu", 2.0), kw.get("rho", 0.0), kw.get("H"))
        alarms = (s_te[a_te == 0] > thr).astype(float)
        hits = (s_te[a_te == 1] > thr).astype(float)
        out["f_err"].append(alarms.mean() - cond["fpr"])
        out["f_nben"].append(alarms.size)
        try:
            _, lo, hi, neff = C.wilson_ess_ci(alarms)
            out["f_ess_se"].append((hi - lo) / 2 / Z); out["f_neff"].append(neff)
        except Exception:
            pass
        _, lo, hi = C.wilson(alarms.sum(), alarms.size)
        out["f_naive_se"].append((hi - lo) / 2 / Z)
        out["r_err"].append(hits.mean() - cond["recall"])
        out["r_natt"].append(hits.size)
        idx = np.flatnonzero(a_te == 1)
        out["r_ncamp"].append(1 + int((np.diff(idx) > 1).sum()) if idx.size else 0)
        try:
            _, lo, hi, neff = C.ess_plugin_ci(hits)
            out["r_ess_se"].append((hi - lo) / 2 / Z); out["r_neff"].append(neff)
        except Exception:
            pass
        out["r_naive_se"].append(hits.std(ddof=1) / np.sqrt(hits.size))
    return {k: np.array(v, float) for k, v in out.items()}


def row(cell, n, metric, err, ess_se, naive_se, neff, ncamp, reps):
    sd = err.std(ddof=1)
    implied = (ess_se.mean() / sd) ** 2 * neff.mean()
    return {"cell": cell, "n": n, "metric": metric, "reps": reps,
            "sd_error": round(float(sd), 5), "bias": round(float(err.mean()), 5),
            "se_aware": round(float(ess_se.mean()), 5),
            "ratio_aware": round(float(ess_se.mean() / sd), 3),
            "se_naive": round(float(naive_se.mean()), 5),
            "ratio_naive": round(float(naive_se.mean() / sd), 3),
            "neff_plugin": round(float(neff.mean()), 1),
            "neff_implied": round(float(implied), 1),
            "neff_overstated": round(float(neff.mean() / implied), 2),
            "mean_campaigns": round(float(ncamp.mean()), 1)}


rows = []
for cell, kw in CELLS.items():
    for n in (5000, 20000):
        d = run(kw, n)
        reps = int(d["f_err"].size)
        rows.append(row(cell, n, "fpr", d["f_err"], d["f_ess_se"], d["f_naive_se"],
                        d["f_neff"], d["r_ncamp"], reps))
        rows.append(row(cell, n, "recall", d["r_err"], d["r_ess_se"], d["r_naive_se"],
                        d["r_neff"], d["r_ncamp"], reps))
df = pd.DataFrame(rows)
df.to_csv("diagnostics/p121_width.csv", index=False)
pd.set_option("display.width", 220)
print(df.to_string(index=False))
print("\nwrote diagnostics/p121_width.csv")
