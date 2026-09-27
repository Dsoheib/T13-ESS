# Runtime audit (P26/P27) — 2026-09-19

## acf is FFT-based (not O(n^2))
`dif.py::acf` uses `np.fft.rfft` / `np.fft.irfft` (Wiener-Khinchin), O(n log n). Verified correct
against a direct O(n^2) computation to < 1e-10 on a 5000-point AR(1)
(`tests/test_core.py::test_acf_fft_matches_direct`). The real-data DIF path (`dif_report` ->
acf-based estimators) is therefore FFT throughout; a 120k-row window will complete.

## Scaling: per-replicate wall time, heaviest cell (bg_ar__lab_campaign, B=200)
| n | per-replicate wall | ratio vs prev (2x n) |
|---|---|---|
| 5000  | 0.272 s | — |
| 10000 | 0.563 s | 2.07x |
| 20000 | 1.149 s | 2.04x |

**Scaling exponent = log(4.22)/log(4) ≈ 1.04 — linear in n.** No O(n^2) term; the block-jackknife
AUC (nb ~ n^{1/3} refits) is negligible against the linear bootstrap terms at these sizes.

## Why n=20000 takes ~75-90 min (not hung, P27)
Expected factorial cost = 6 scenarios x 500 reps x ~1.15 s (heaviest cell; lighter cells less)
≈ 58 min, run CONCURRENTLY with the 2x2 job (2 x 500 x ~1.15 s ≈ 19 min), so CPU contention
stretches both. This matches the observed wall time; the job is progressing, not stalled. No
relaunch is warranted (no O(n^2) bug to fix).

## Instrumentation added going forward
Per-replicate cost is now known (~1.15 s at n=20000), so any future run's ETA = R x cost x
n_scenarios; a job exceeding ~2x that is the "hung vs slow" threshold.
