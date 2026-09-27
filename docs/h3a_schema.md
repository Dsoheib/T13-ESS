> **RETIRED 2026-09-24 (P125). This schema was never exercised and its instrument was
> removed from the release.** H3a required coding per-claim estimates and standard errors
> from published papers; the in-frame pool resolved only 5 of 16 records to full text, so
> `corpus/claims.csv` was never populated and has been deleted rather than shipped empty.
> Independently, `docs/calibration_findings.md` found that inflating a reported SE by
> sqrt(stream DIF) is not justified by the loss-difference's own dependence (differential
> and stream DIF diverge by two orders of magnitude), so the summary-only survival arm this
> schema depends on was dropped in prereg v0.6. `src/t13/audit.py` and `scripts/survival.py`
> implemented that dropped arm and were removed at submission; both remain reachable at git
> tag `sim-frozen`. This file is kept as the record of what was pre-registered, not as a
> description of the released instrument.

# H3a extraction + reporting schema (n_eff-primary, continuous) — rev 2026-09-20 (P53–P55)

Supersedes the banded version. The reportable quantity is **n_eff and the interval-width
understatement k = sqrt(DIF)** — continuous, no ordinal bands (the project's spine is n_eff, not
an inflation-factor cut, and no threshold is set from the observed magnitudes).

## 1. Governing series (by metric class)
| metric reported | metric_class | governing series |
|---|---|---|
| FPR / alarm rate / specificity | conditional | benign alarm-indicator @ operating threshold |
| recall / TPR @ threshold | conditional | attack score-exceedance (hits) indicator |
| accuracy / precision / F1 | prevalence_dependent | label sequence |
| AUC / AUROC / AUPRC | rank | detector score sequence |

## 2. Per-claim quantities (continuous; no bands)
Extract: n_test, and the reported interval half-width h_reported (from CI, SE→1.96·SE, or error
bar). Then:
- **dif_used = a RANGE [dif_lo, dif_hi]** (P55 — DIF is feature- and capture-dependent; a point
  value would be false precision). Matching rule, most-specific first:
  1. exact cell measured — (this dataset, this grain, this feature-class) across the measured
     days/windows → range = [min, max] over those cells; `dif_source=exact`.
  2. same grain + feature-class, measured on OTHER datasets → cross-dataset range for that
     feature-class; `dif_source=cross-dataset`.
  3. no matching cell (feature-class never measured at that grain) → `dif_source=none` →
     the claim is **NOT-ASSESSABLE (unmeasured)**.
- **n_eff = n_test / dif_used** → a range [n_test/dif_hi, n_test/dif_lo].
- **k = sqrt(dif_used)** → range [sqrt(dif_lo), sqrt(dif_hi)] = "the reported interval is k× narrower
  than its dependence-corrected width."
- **h_corrected = k · h_reported** → range.

Report the CONSERVATIVE end (dif_lo → smallest k) as a lower bound on understatement, and the full
range beside it. A claim is counted as understated only to the extent guaranteed by dif_lo.

## 3. NOT-ASSESSABLE (kept; its count is a headline in its own right, P28)
A claim is NOT-ASSESSABLE if EITHER:
- the release used is order-destroyed (MachineLearningCVE; CICIoMT2024 no-timestamp; balanced
  samples; any dataset failing time_order_audit) → no DIF is measurable on the release the authors
  used; OR
- n_eff (upper end, n_test/dif_lo) < 50 → below the H7 floor; no interval is defensible, report
  n_eff not a verdict.
The NOT-ASSESSABLE fraction is reported as a primary result (the release-practice / uncorrectability
finding), separately from the assessable distribution.

## 4. H3a headline — a distribution, not a fraction (P54)
Among ASSESSABLE claims, report the DISTRIBUTION of k (and of n_eff): e.g. "the median reported
interval is k_med× narrower than its dependence-corrected width [IQR …]", per stratum (core /
volume / preprint) and pooled, with the NOT-ASSESSABLE count beside it. No ordinal bands, no
threshold. If a single sentence is wanted: the median k and the fraction with k>2 (interval less
than half its corrected width) MAY be quoted as descriptive, but k>2 is stated as "interval < half
corrected width" (interval-width semantics), not as a preregistered severity cut.

## 5. claims.csv fields
paper_id, venue, stratum, year, dataset, distribution_used, grain, split, metric, metric_class,
model_a, model_b, est_a, est_b, se_a, se_b, n_test, ci_method, data_released, governing_series,
dif_lo, dif_hi, dif_source, n_eff_lo, n_eff_hi, k_lo, k_hi, h_reported, h_corrected_lo,
h_corrected_hi, assessable, claim_text.
