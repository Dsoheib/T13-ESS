"""P96 sensitivity: re-run the factorial at the preregistered B=1000 (vs the B=200 run of
record) and test whether any bootstrap-dependent reported coverage moves beyond its MC SE.
The FPR (Wilson-on-n_eff), naive-normal recall and ESS recall intervals contain no bootstrap
and are B-independent by construction; only the AUC columns (naiveBoot, mbb) and the *_mbb rows
depend on B. Same n, R, seed, scenarios as the canonical run_coverage_sim (n=5000, R=500).
Writes results/coverage_sim_B1000.csv and prints the comparison. Does NOT touch the canonical
results/coverage_sim.csv.
"""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import run, FACTORIAL

SCN = FACTORIAL + ["lrd_H0.8", "heavy_tail"]
import os
OUT = "results/coverage_sim_B1000.csv"
if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
    df1000 = pd.read_csv(OUT)                       # reuse a prior B=1000 run (reproducible, fast)
else:
    df1000, _ = run(scenarios=SCN, n=5000, R=500, B=1000, seed=0, split="temporal")
    df1000.to_csv(OUT, index=False)

base = pd.read_csv("results/coverage_sim.csv")  # B=200 run of record (Table 1)
# The ONLY B-dependent cells REPORTED in the paper are the AUC columns of Table 1
# (naiveBoot, mbb). Reported FPR is Wilson-on-n_eff and reported recall is naive-normal / ESS
# plug-in -- no bootstrap, B-independent. recall-mbb and fpr-mbb are computed but not tabulated.
REPORTED = {("auc", "naiveBoot"), ("auc", "mbb")}
boot = df1000[df1000.interval.isin(["naiveBoot", "mbb"])].copy()
rep_rows, diag_rows, moved_rep, moved_diag = [], [], 0, 0
for _, r in boot.iterrows():
    b = base[(base.scenario == r.scenario) & (base.metric == r.metric) & (base.interval == r.interval)]
    if not len(b):
        continue
    c200, se200 = float(b.cov_uncond.iloc[0]), float(b.mc_se_uncond.iloc[0])
    c1000, se1000 = float(r.cov_uncond), float(r.mc_se_uncond)
    d = c1000 - c200
    comb_se = float(np.sqrt(se200**2 + se1000**2))
    flag = "MOVED" if abs(d) > comb_se else ""
    line = (f"{r.scenario:22s} {r.metric:6s} {r.interval:10s} "
            f"B200={c200:.3f}±{se200:.3f}  B1000={c1000:.3f}±{se1000:.3f}  "
            f"delta={d:+.3f}  combSE={comb_se:.3f}  {flag}")
    if (r.metric, r.interval) in REPORTED:
        rep_rows.append(line); moved_rep += bool(flag)
    else:
        diag_rows.append(line); moved_diag += bool(flag)
print("\n=== P96 sensitivity: B=200 (record) vs B=1000 (prereg), n=5000, R=500 ===")
print("\n-- REPORTED cells (AUC columns of Table 1) --")
print("\n".join(rep_rows))
print(f"REPORTED cells moving beyond combined MC SE: {moved_rep} / {len(rep_rows)}")
print("\n-- non-reported diagnostic bootstrap cells (recall-mbb, fpr-mbb; not tabulated) --")
print("\n".join(diag_rows))
print(f"diagnostic cells moving beyond combined MC SE: {moved_diag} / {len(diag_rows)}")
print("\nVERDICT:", "REGENERATE tables from B=1000" if moved_rep else
      "no REPORTED coverage moves beyond MC SE; B=200 stands (one line in Limitations)")
