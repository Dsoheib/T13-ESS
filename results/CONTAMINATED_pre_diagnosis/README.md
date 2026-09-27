# CONTAMINATED results — do not use

These CSVs come from `scripts/run_coverage_sim.py` / `run_split_2x2.py` / `run_floor_curve.py`
BEFORE the 2026-09-19 diagnosis. They are invalid because of two defects found in that run:

1. **Estimand mismatch.** Coverage for threshold-dependent metrics (FPR, recall, accuracy)
   was scored against the *unconditional population* truth, but a test-set interval targets
   the metric at the *training-learned threshold* (the threshold-conditional truth). This
   alone drove the iid control to 0.81 instead of ~0.95.
2. **Rare-event interval.** FPR (~1%) used the normal / ESS-plugin interval, which
   under-covers near 0 even against the right estimand; the Wilson interval is required.

Diagnosis: `diagnostics/p1_estimand.py` (three-estimand table), `diagnostics/p4_tau_vs_n.py`
(estimator is sound: AR(1) tau_hat = 19 flat in n). Corrected experiment:
`diagnostics/corrected_coverage.py` -> the new `results/coverage_sim.csv`.
