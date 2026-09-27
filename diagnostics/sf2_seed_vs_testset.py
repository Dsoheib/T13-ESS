"""SF-2 simulation (P70): seed/rerun dispersion is a different estimand than test-set sampling
uncertainty, and the reported seed-based interval shrinks toward zero as the seed count rises while
the true sampling uncertainty stays put. Additive analysis against the FROZEN instrument
(t13.sim.generate, t13.ci) -- sim.py/dif.py/ci.py unchanged (sim-frozen).

Design: ONE fixed test set. 'Seeds' = re-learning the operating threshold on a fresh training draw
each seed (model-fitting instability), evaluated on the SAME fixed test set. Report, vs seed count K:
  seed_std   = std of the metric across K seeds (model-fitting dispersion; a fixed quantity)
  seed_SE    = seed_std / sqrt(K)  (what 'mean +/- std/sqrt(K)' or a seed-CI reports) -> shrinks ->0
  testset_sd = block-bootstrap std of the metric on the fixed test set (the true sampling
               uncertainty of the metric) -> constant in K
Divergence of seed_SE (->0) from testset_sd (constant) is the SF-2 result.
"""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, SCENARIOS
from t13 import ci as C

def run(scenario="bg_ar__lab_campaign", n=5000, fpr=0.01, Ks=(2,5,10,20,50,100,200), B=300, seed=0):
    kw = SCENARIOS[scenario]; rng = np.random.default_rng(seed)
    # ONE fixed test set
    a_te, s_te = generate(n, rng=rng, **kw)
    fp = C.fpr_at_threshold; rec = C.recall_at_threshold
    # true test-set sampling uncertainty (block bootstrap on the fixed test set), threshold fixed at pop
    thr0 = np.quantile(s_te[a_te == 0], 1 - fpr) if (a_te==0).any() else 0.0
    est, lo, hi, *_ = C.block_bootstrap_ci(a_te, s_te, C.fpr_at_threshold(thr0), B=B, rng=rng, kind="basic")
    testset_sd = (hi - lo) / (2*1.96)   # half-width -> sd
    # seed dispersion: re-learn threshold on a fresh training draw each seed, eval on FIXED test set
    Kmax = max(Ks); metric_by_seed = []
    for k in range(Kmax):
        a_tr, s_tr = generate(n, rng=rng, **kw)
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr) if (a_tr==0).any() else thr0
        metric_by_seed.append(float(np.mean(s_te[a_te == 0] > thr)))  # FPR on FIXED test set
    metric_by_seed = np.array(metric_by_seed)
    rows = []
    for K in Ks:
        m = metric_by_seed[:K]
        seed_std = m.std(ddof=1); seed_SE = seed_std / np.sqrt(K)
        rows.append({"K_seeds": K, "seed_std": round(seed_std,5), "seed_SE": round(seed_SE,5),
                     "testset_sd(true)": round(testset_sd,5),
                     "seed_SE / testset_sd": round(seed_SE/testset_sd,3) if testset_sd>0 else np.nan})
    return pd.DataFrame(rows), testset_sd

if __name__ == "__main__":
    df, tsd = run()
    pd.set_option("display.width",160); print(df.to_string(index=False))
    print(f"\ntrue test-set sampling sd (block bootstrap, constant in K) = {tsd:.5f}")
    print("SF-2: seed_SE -> 0 as K grows while testset_sd is constant -> a field reporting seed "
          "mean+/-std/sqrt(K) drives its stated uncertainty to zero, never estimating the metric's "
          "sampling uncertainty. seed_std itself is the model-fitting component, a different estimand.")
    df.to_csv("diagnostics/sf2_seed_vs_testset.csv", index=False)
