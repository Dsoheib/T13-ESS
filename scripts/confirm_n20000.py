"""n=20000 confirmation, run SEQUENTIALLY in one process (no concurrency contention).
Four factorial cells (the pattern) + the 2x2 (H6). Writes dedicated *_n20000.csv files so the
n=5000 canonical results are preserved. Prints per-cell wall time for progress (P27)."""
import sys, time; sys.path.insert(0, "src")
import pandas as pd
from t13.sim import coverage_run, SCENARIOS, FACTORIAL

N, R, B = 20000, 500, 150   # B=150: coverage is R-limited; keeps the sequential run in budget
frames, metas = [], []
for name in FACTORIAL:                       # iid, campaigns_only, background_only, both
    t = time.time()
    df, meta = coverage_run(name, SCENARIOS[name], n=N, R=R, B=B, seed=0, split="temporal", include_episode=False)
    frames.append(df); metas.append(meta)
    print(f"[factorial] {name} done in {time.time()-t:.0f}s", flush=True)
pd.concat(frames, ignore_index=True).to_csv("results/coverage_sim_n20000.csv", index=False)
pd.DataFrame(metas).to_csv("results/coverage_sim_n20000_meta.csv", index=False)
print("factorial written", flush=True)

sp = []
for split in ("random", "temporal"):
    t = time.time()
    df, _ = coverage_run("bg_ar__lab_campaign", SCENARIOS["bg_ar__lab_campaign"], n=N, R=R, B=B, seed=0, split=split, include_episode=False)
    sp.append(df); print(f"[2x2] {split} done in {time.time()-t:.0f}s", flush=True)
pd.concat(sp, ignore_index=True).to_csv("results/split_2x2_n20000.csv", index=False)
print("2x2 written; confirmation complete", flush=True)
