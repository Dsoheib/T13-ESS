"""P102: re-run ONLY the reported AUC cells (naiveBoot, mbb) at the run-of-record n=20000, B=1000,
against the B=150 confirmation. Also reports the iid-control AUC at B=1000 specifically (small-B
percentile intervals undercover, so part of the ~0.93 control undercoverage may be a B artefact).
Lean: reuses the generator and the two AUC interval routines only -- no FPR/recall/episode/jackknife.
Writes results/p102_auc_n20000.csv and prints the comparison.
"""
import sys, time, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, population_truth, SCENARIOS, FACTORIAL
import t13.ci as C

_ap = argparse.ArgumentParser()
_ap.add_argument("--R", type=int, default=500); _ap.add_argument("--n", type=int, default=20000)
_ap.add_argument("--scenarios", nargs="*", default=FACTORIAL + ["lrd_H0.8", "heavy_tail"])
_a = _ap.parse_args()
N, R, B, SEED = _a.n, _a.R, 1000, 0
SCN = _a.scenarios
conf = pd.read_csv("results/coverage_sim_n20000.csv")  # B=150 confirmation (temporal)

def auc_cov(name, kw):
    pop = population_truth(0.01, **kw); truth = pop["auc"]
    rng = np.random.default_rng(SEED)
    nb = {"naiveBoot": [0, 0], "mbb": [0, 0]}  # [n_computable, n_cover]
    for _ in range(R):
        a, s = generate(2 * N, rng=rng, **kw)
        a_te, s_te = a[N:], s[N:]
        for iv, fn in (("naiveBoot", lambda: C.naive_iid_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng)[1:]),
                       ("mbb", lambda: C.block_bootstrap_ci(a_te, s_te, C.auc, B=B, rng=rng, kind="basic")[1:3])):
            try:
                lo, hi = fn()
                if lo is not None and hi is not None and not (np.isnan(lo) or np.isnan(hi)):
                    nb[iv][0] += 1; nb[iv][1] += int(lo <= truth <= hi)
            except Exception:
                pass
    out = {}
    for iv, (nc, cov) in nb.items():
        cu = cov / R
        out[iv] = (round(cu, 3), round(float(np.sqrt(cu * (1 - cu) / R)), 3))
    return out

rows = []
for name in SCN:
    t = time.time()
    o = auc_cov(name, SCENARIOS[name])
    for iv in ("naiveBoot", "mbb"):
        c1000, se = o[iv]
        b150 = conf[(conf.scenario == name) & (conf.metric == "auc") & (conf.interval == iv)]
        c150 = float(b150.cov_uncond.iloc[0]) if len(b150) else float("nan")
        se150 = float(b150.mc_se_uncond.iloc[0]) if len(b150) else float("nan")
        d = c1000 - c150; cse = float(np.sqrt(se**2 + se150**2)) if not np.isnan(se150) else float("nan")
        rows.append(dict(scenario=name, interval=iv, cov_B150=c150, cov_B1000=c1000,
                         mc_se_B1000=se, delta=round(d, 3), comb_se=round(cse, 3),
                         moved="MOVED" if (not np.isnan(cse) and abs(d) > cse) else ""))
    print(f"[{name}] done in {time.time()-t:.0f}s", flush=True)

df = pd.DataFrame(rows); df.to_csv("results/p102_auc_n20000.csv", index=False)
pd.set_option("display.width", 200)
print("\n=== P102: AUC coverage at n=20000, B=1000 vs B=150 confirmation ===")
print(df.to_string(index=False))
ctrl = df[(df.scenario == "bg_iid__lab_scatter")]
print("\niid-control AUC at B=1000:")
print(ctrl.to_string(index=False))
print(f"\ncells moving beyond combined MC SE: {(df.moved=='MOVED').sum()} / {len(df)}")
