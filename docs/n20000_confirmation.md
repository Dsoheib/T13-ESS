# n=20000 confirmation (2026-09-19)

Confirmatory run at n=20000, R=500, B=150, seed 0, on the FIXED code (block_jackknife_auc
capped). Sequential (no concurrency). `results/coverage_sim_n20000.csv`, `split_2x2_n20000.csv`.
Episode bootstrap excluded from this run (O(episodes*B); its behaviour is set by episode count,
characterised in p13, not by n). Headline = cov_uncond (non-computable = miss).

## Factorial — pattern reproduced, no cell reverses direction

| cell (bg / labels) | FPR naive→corr | recall naive→ESS | AUC naive→mbb | comp_rate(recall) |
|---|---|---|---|---|
| iid / scatter (control) | 0.956→0.958 | 0.954→0.964 | 0.930→0.926 | 1.00 |
| iid / campaign | 0.946→0.950 | 0.946→0.954 | 0.912→0.894 | 0.99 |
| AR / scatter | **0.556→0.944** | 0.908→0.950 | 0.916→0.950 | 1.00 |
| AR / campaign | **0.580→0.948** | **0.484→0.876** | **0.374→0.864** | 1.00 |

Compare n=5000 (DIAGNOSIS_REPORT_v2): iid control ~0.95; FPR broken by background only
(0.60/0.59) and repaired (0.92/0.93); recall/AUC broken in the AR/campaign cell (0.32/0.32),
corrections partial (0.78/0.78). At n=20000 the SAME directions hold and the corrections recover
BETTER (recall both 0.876 vs 0.775; AUC both 0.864 vs 0.777) because more independent episodes
at larger n lift the episode floor — consistent with SF-H5/H7, not a contradiction.

Notable: campaigns_only recall computability rises 0.74 (n=5000) → 0.99 (n=20000): the earlier
uncond/cond gap was a small-window artifact (few attacks per window), now resolved. The P9
dual-reporting correctly flagged it as finite-window, not a coverage defect.

## 2x2 (H6) — confirmed

| split | FPR naive | FPR corrWilson (±MC SE) |
|---|---|---|
| random | 0.708 | 0.714 ± 0.020 |
| temporal | 0.580 | **0.948 ± 0.010** |

Temporal-corrected > random-corrected, non-overlapping (matches n=5000: 0.922 vs 0.732). Under
random split the correction is a no-op (0.708→0.714); temporal makes it work (0.580→0.948).

## Verdict
n=20000 reproduces the n=5000 factorial and 2x2 pattern qualitatively; no cell reverses. The
simulation phase result is stable across n. (Runtime note: the earlier n=20000 stall was
block_jackknife_auc doing ~n/2 refits at small block length; fixed by capping blocks — see
docs/runtime_audit.md.)

## P96 sensitivity: B=1000 vs the B=150/B=200 runs of record (2026-09-22)

The prereg fixes B=1000; the reported runs used B=200 (Table 1, n=5000) and B=150 (Table 2,
n=20000). Deviation logged in prereg/CHANGELOG.md (reason: runtime). Re-ran the factorial at
n=5000, R=500, B=1000 (scripts/sensitivity_B1000.py -> results/coverage_sim_B1000.csv) and
compared to the B=200 record against combined MC SE.

- **Reported bootstrap cells** = the AUC columns of Table 1 (naiveBoot, mbb). **0/12 moved**
  beyond combined MC SE. Largest AUC shift: lrd_H0.8 mbb, -0.028 (combSE 0.031) -- within noise.
- **Non-reported diagnostic cells** (recall-mbb, fpr-mbb; not tabulated): 2/12 moved --
  bg_ar/scatter recall-mbb +0.030 and heavy_tail recall-mbb +0.054, **both toward better
  coverage**. Reported recall uses naive-normal / ESS (no bootstrap).
- **FPR** intervals (Wilson-on-n_eff) and the 0.948/0.714 split headline contain no bootstrap
  and are B-independent by construction.

**Verdict:** no reported coverage moves beyond MC SE; the B=200/B=150 tables stand. Recorded as
one line in the paper's Limitations. sim-frozen and prereg-v1 untouched.
