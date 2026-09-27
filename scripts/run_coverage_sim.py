"""Canonical coverage experiment (dual-reported, correct estimand + Wilson FPR).
Writes results/coverage_sim.csv (long format, per-cell MC SE, computability rate) and
results/coverage_sim_meta.csv. No figures (paper is unbuilt by reviewer order)."""
import sys, argparse; sys.path.insert(0, "src")
import pandas as pd
from t13.sim import run, FACTORIAL

p = argparse.ArgumentParser()
p.add_argument("--scenarios", nargs="*", default=FACTORIAL + ["lrd_H0.8", "heavy_tail"])
p.add_argument("--n", type=int, default=5000); p.add_argument("--R", type=int, default=500)
p.add_argument("--B", type=int, default=200); p.add_argument("--seed", type=int, default=0)
p.add_argument("--split", default="temporal")
a = p.parse_args()
df, meta = run(scenarios=a.scenarios, n=a.n, R=a.R, B=a.B, seed=a.seed, split=a.split)
df.to_csv("results/coverage_sim.csv", index=False)
meta.to_csv("results/coverage_sim_meta.csv", index=False)
pd.set_option("display.width", 200)
print(df.to_string(index=False)); print(); print(meta.to_string(index=False))
