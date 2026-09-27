"""Long-memory boundary: coverage across a grid of Hurst exponents.

Additive. It does not modify the frozen instrument: `t13.sim.coverage_run` is called with
scenario kwargs built here, so `SCENARIOS` and `sim.py` are untouched.

The H=0.8 arm uses the same seed, n, R and B as the reported `lrd_H0.8` cell in
results/coverage_sim.csv, so that arm must reproduce it. scripts/check_abstract.py enforces this.

Writes results/hurst_sweep.csv and results/hurst_sweep_meta.csv.
"""
import sys, argparse, time
sys.path.insert(0, "src")
import pandas as pd
from t13.sim import coverage_run, SCENARIOS

p = argparse.ArgumentParser()
p.add_argument("--H", nargs="*", type=float, default=[0.6, 0.7, 0.8, 0.9])
p.add_argument("--n", type=int, default=5000)
p.add_argument("--R", type=int, default=500)
p.add_argument("--B", type=int, default=200)
p.add_argument("--seed", type=int, default=0)
a = p.parse_args()

# The reported long-memory cell, with H as the only thing that varies.
base = dict(SCENARIOS["lrd_H0.8"])
frames, metas = [], []
for H in a.H:
    kw = dict(base, H=H)
    t0 = time.time()
    df, meta = coverage_run(f"lrd_H{H:g}", kw, n=a.n, R=a.R, B=a.B, seed=a.seed, split="temporal")
    df["H"] = H
    meta["H"] = H
    frames.append(df); metas.append(meta)
    # Wall time is reported to the console but deliberately kept OUT of the committed CSV:
    # it is machine-dependent, so recording it would dirty the tree on every rerun and make
    # the artifact look non-reproducible when every scientific value is identical.
    print(f"H={H:g} done in {time.time() - t0:.1f}s", flush=True)

out = pd.concat(frames, ignore_index=True)
out.to_csv("results/hurst_sweep.csv", index=False)
pd.DataFrame(metas).to_csv("results/hurst_sweep_meta.csv", index=False)
print(out[out.metric.eq("fpr")].to_string(index=False))
