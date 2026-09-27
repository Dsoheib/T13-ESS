"""H6 test: random vs temporal split, under the CORRECTED estimand, R>=500, dual-reported.
Writes results/split_2x2.csv. Verdict is read off cov_uncond for FPR:
H6 predicts temporal-corrected > random-corrected with non-overlapping MC SE."""
import sys, argparse; sys.path.insert(0, "src")
import pandas as pd
from t13.sim import coverage_run, SCENARIOS

p = argparse.ArgumentParser()
p.add_argument("--scenario", default="bg_ar__lab_campaign")
p.add_argument("--n", type=int, default=5000); p.add_argument("--R", type=int, default=500)
p.add_argument("--B", type=int, default=200); p.add_argument("--seed", type=int, default=0)
a = p.parse_args()
frames = []
for split in ("random", "temporal"):
    df, _ = coverage_run(a.scenario, SCENARIOS[a.scenario], n=a.n, R=a.R, B=a.B, seed=a.seed, split=split)
    frames.append(df)
out = pd.concat(frames, ignore_index=True)
out.to_csv("results/split_2x2.csv", index=False)
pd.set_option("display.width", 200)
print(out.to_string(index=False))
