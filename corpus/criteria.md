# Screening criteria (verbatim, Option A) -- ships with the artifact

ASCII-only (no en-dashes, to avoid the U+2013 corruption that damaged the prior B-packet copy).
Screened single-coder; every record logged in inclusion_log.csv with decision, reason, criterion
invoked, distribution_used. Mark `unclear` where the paper genuinely does not say.

## Inclusion criteria (from frozen prereg-v1)
A record is INCLUDED iff ALL of:
1. Domain: IoT or IoMT network intrusion detection (NIDS).
2. Years: published 2024 to 2026 (inclusive).
3. Venue frame: Computers & Security, JNCA, IEEE TNSM, IEEE IoT-J, TIFS, USENIX Security, CCS,
   NDSS (core stratum); OR Sensors, Electronics, Scientific Reports (volume stratum); OR a
   preprint (arXiv / preprints.org), flagged `preprint` and reported as a sub-stratum (P52 rule;
   a published version in a frame venue supersedes its preprint).
4. Uncertainty reported: the paper reports a confidence interval, standard error, error bar, OR a
   significance test (t-test / Wilcoxon / etc.) on a detection metric.
5. Public dataset: evaluated on a public benchmark.

EXCLUDE if any criterion fails; record the FIRST failing criterion (1-5) as `criterion_invoked`.

## Field definitions
- `time_aware_split` (yes/no/unclear): does the paper use a temporal / time-aware / chronological
  train-test split (vs random split or k-fold)? -- resolved from FULL TEXT; H1's population is the
  subset with yes. Venue is NOT a filter on this (P59): a Sensors paper with a chronological split
  is a full member; a TIFS paper with a random split is not.
- `reports_ci_or_test` (yes/no/unclear): criterion 4, from full text.
- `public_dataset`: name(s) or none.
- `time_order_recoverable` (yes/no/na): from the release used.
- `distribution_used`: which release/distribution of the dataset (e.g. CICIDS2017
  `GeneratedLabelledFlows` timestamped vs `MachineLearningCVE` timestamp-dropped; MAWIFlow
  `full-parquet` vs `balanced-sample`; CICIoMT2024 `flow-csv-no-timestamp`), or `unclear`.
- `include` (include/exclude); `criterion_invoked` (1-5 or blank).

## Reliability (Option A, elected)
Single-coder; no kappa claimed. Inter-rater reliability not established (no eligible independent
coder). Reproducibility rests on this verbatim criteria file + the published inclusion_log.csv.
Abstract-stage decisions are superseded by full-text confirmation. Supervisor performs adversarial
review (challenge of the hardest decisions) -- supervision, not reliability.
