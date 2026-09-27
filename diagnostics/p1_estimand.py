"""P1 diagnosis: which estimand does a test-set interval actually cover?

For the iid scenario, learn the threshold on the training half and compute intervals on the
test half, then score coverage against THREE truths:
  pop  = unconditional population metric (threshold learned on a huge sample)
  win  = window-conditional metric (E[metric_hat | non-degenerate test window])
  cond = threshold-conditional metric (exact metric at the REALISED learned threshold)
Metrics: FPR@thr and recall@thr are threshold-dependent; AUC is threshold-free (pop==cond).
Intervals: naive (correction OFF) and ESS plug-in / MBB (correction ON).
Every cell reports coverage with Monte-Carlo SE = sqrt(p(1-p)/R_used).
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, population_truth, window_truth, conditional_truth, SCENARIOS
from t13 import ci as C


def cov_se(hits):
    h = np.asarray(hits, float); R = h.size; p = h.mean()
    return p, np.sqrt(p * (1 - p) / R), R


def run(scenario="iid", n=5000, R=1000, B=400, fpr=0.01, seed=0, min_pos=20):
    kw = SCENARIOS[scenario]
    pop = population_truth(fpr, **kw)
    win = window_truth(n, fpr, R=min(600, 4 * R), **kw)
    rng = np.random.default_rng(seed)
    rec = {k: [] for k in
           ["fpr_naive_pop", "fpr_naive_win", "fpr_naive_cond",
            "fpr_ess_pop", "fpr_ess_win", "fpr_ess_cond",
            "fpr_wilson_cond", "fpr_mbb_cond",
            "rec_naive_pop", "rec_naive_win", "rec_naive_cond",
            "rec_ess_pop", "rec_ess_win", "rec_ess_cond",
            "auc_naive_pop", "auc_mbb_pop"]}
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < min_pos or a_te.sum() < min_pos or (a_te == 0).sum() < min_pos:
            continue
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr)
        cond = conditional_truth(thr, kw.get("mu", 2.0), kw.get("rho", 0.0), kw.get("H"))
        # ---- FPR ----
        alarms = (s_te[a_te == 0] > thr).astype(float)
        _, lo, hi = C.naive_normal_ci(alarms)
        rec["fpr_naive_pop"].append(lo <= pop["fpr"] <= hi)
        rec["fpr_naive_win"].append(lo <= win["fpr"] <= hi)
        rec["fpr_naive_cond"].append(lo <= cond["fpr"] <= hi)
        _, lo, hi, _ = C.ess_plugin_ci(alarms)
        rec["fpr_ess_pop"].append(lo <= pop["fpr"] <= hi)
        rec["fpr_ess_win"].append(lo <= win["fpr"] <= hi)
        rec["fpr_ess_cond"].append(lo <= cond["fpr"] <= hi)
        _, lo, hi, _ = C.wilson_ess_ci(alarms)
        rec["fpr_wilson_cond"].append(lo <= cond["fpr"] <= hi)
        _, lo, hi, *_ = C.block_bootstrap_ci(a_te, s_te, C.fpr_at_threshold(thr), B=B, rng=rng, kind="basic")
        rec["fpr_mbb_cond"].append(lo <= cond["fpr"] <= hi)
        # ---- recall ----
        hits = (s_te[a_te == 1] > thr).astype(float)
        _, lo, hi = C.naive_normal_ci(hits)
        rec["rec_naive_pop"].append(lo <= pop["recall"] <= hi)
        rec["rec_naive_win"].append(lo <= win["recall"] <= hi)
        rec["rec_naive_cond"].append(lo <= cond["recall"] <= hi)
        _, lo, hi, _ = C.ess_plugin_ci(hits)
        rec["rec_ess_pop"].append(lo <= pop["recall"] <= hi)
        rec["rec_ess_win"].append(lo <= win["recall"] <= hi)
        rec["rec_ess_cond"].append(lo <= cond["recall"] <= hi)
        # ---- AUC (threshold-free: pop==cond) ----
        _, lo, hi = C.naive_iid_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng)
        rec["auc_naive_pop"].append(lo <= pop["auc"] <= hi)
        _, lo, hi, *_ = C.block_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng, kind="basic")
        rec["auc_mbb_pop"].append(lo <= pop["auc"] <= hi)
    rows = []
    for k, v in rec.items():
        p, se, Ru = cov_se(v)
        metric, interval, estimand = k.split("_")
        rows.append({"metric": metric, "interval": interval, "estimand": estimand,
                     "coverage": round(p, 3), "mc_se": round(se, 3), "R_used": Ru})
    return pd.DataFrame(rows), {"pop": pop, "win": win}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="iid"); ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--R", type=int, default=1000); ap.add_argument("--B", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    df, truths = run(a.scenario, a.n, a.R, a.B, seed=a.seed)
    pd.set_option("display.width", 160)
    print(f"scenario={a.scenario} n_test={a.n} R={a.R} B={a.B}")
    print("truth fpr: pop=%.4f win=%.4f | recall: pop=%.4f win=%.4f | auc pop=%.4f"
          % (truths['pop']['fpr'], truths['win']['fpr'], truths['pop']['recall'],
             truths['win']['recall'], truths['pop']['auc']))
    print(df.to_string(index=False))
    df.to_csv(f"diagnostics/p1_{a.scenario}.csv", index=False)
