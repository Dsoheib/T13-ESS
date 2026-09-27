# Corpus feasibility count (2026-09-19) — screening unblocked

Screening is unblocked because `distribution_used` (P28) and H3a's n_eff keying are required
regardless of H2's value. First-pass count below; full coding + Cohen's κ needs the second coder.

## Sampling frame — per PREREG venues x years (P38 correction)
The frame is defined by the prereg, NOT inherited from Lew (whose corpus was selected for
deployment-oriented criteria — inheriting it would import that inclusion bias into H1's denominator):
- **Venues:** Computers & Security, JNCA, IEEE TNSM, IEEE IoT-J, TIFS, USENIX Sec, CCS, NDSS
  (core stratum) + Sensors, Electronics, Scientific Reports (volume stratum).
- **Years:** 2024–2026. **Inclusion:** IoT/IoMT NIDS; reports CI/SE/error-bar/significance test on
  a detection metric; public dataset. `distribution_used` recorded for every included paper.
- Enumeration is by per-venue / database query against these venues+years (to be completed with the
  second coder). **Lew et al. 2026's 29 papers are cross-checked as a SCREENED SUBSET**, flagged
  `sampling-frame-crosscheck`, not used as the frame.

## First-pass feasibility count (single coder)
Targeted searches over the frame surfaced ~10 distinct 2024–2026 IoT/IoMT NIDS papers reporting
uncertainty (corpus/inclusion_log.csv): Sci Rep 2026 (Wilcoxon + Cohen's d over 5 random seeds),
arXiv 2604.06254 / 2605.16707 / 2509.10563 / 2502.11470 / 2506.18114, ScienceDirect
S1389128626003713, Frontiers fmed 2025, "Hidden Variable" 2026 (i.i.d. bootstrap CIs).
- **Feasibility verdict: ACHIEVABLE.** These plus systematic per-venue querying comfortably reach
  the target N ≈ 40–60; the ≥ 25 auditable-papers threshold is clearly met. This first-pass count
  is a LOWER BOUND (two searches, not the full per-venue sweep).

## Early signal on H1 (do not touch thresholds; observational)
Every candidate whose method is visible reports uncertainty from **random-seed reruns or random
splits** (e.g. "5 independent runs with different seeds", i.i.d. bootstrap, Wilcoxon over runs) —
i.e. under an exchangeability assumption, with **no within-test-set dependence correction**. This
is consistent with H1 (fraction correcting for dependence < 20%, likely ≈ 0), but the count is
not frozen until two-coder screening completes.

## Early signal on P28 distribution_used
Several candidates evaluate on **CICIoMT2024** (no timestamp column → order-destroyed form) or on
**MachineLearningCVE / balanced samples**. This is direct first evidence for the release-practice
claim: the corpus predominantly consumes the order-destroyed derivative even where an orderable
release exists (CICIDS2017 GeneratedLabelledFlows). `distribution_used` will quantify it.

## κ status (honest)
Cohen's κ requires two independent coders (prereg: two coders). Only one coder (this pass) has
screened; **κ is pending the second coder (Sabri / Okba).** The 10 logged rows are a
single-coder first pass with `unknown-needs-fulltext` marked where the snippet was insufficient —
they are candidates to be double-coded, not final inclusions.

## Next (once double-coded)
For each included claim, extract per the v0.6 schema incl. `distribution_used`, metric_class,
reported interval/SE, n_test, data_released, and the governing series for n_eff/DIF (H3a).

## Update 2026-09-20 — pool deepened to N=53; core stratum = 8 (P51)
Core-venue records (C&S/JNCA/TNSM/IoT-J/TIFS + Computer Networks/ESWA/J.Franklin): **8**
(ieee-tnsm-cvt-2024, ieee-tnsm-dm-ids-2025, ieee-tnsm-logfit-2024, SD-S1389128626003713,
SD-S2542660525001453, SD-S0016003224008615, SD-S1084804524001577, eswa-flowtransformer-2024).
**SUPERSEDED 2026-09-20 (P59):** venue is NOT the denominator. H1's population is
practice-defined (time-aware split + reported uncertainty); the sharp claim runs against the
TIME-AWARE SUBSET of the full pool, with venue strata shown beside it as a descriptive breakdown,
never as a filter. The thin core count does NOT demote the claim. Core enumeration returns only
via the P56 trigger (zero core records in the time-aware subset). See CHANGELOG 2026-09-20 P59/P60.
