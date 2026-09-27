# Claim-extraction codebook (two coders; Cohen's kappa on inclusion and on ci_method)

## Inclusion (all must hold)
1. IoT / IoMT / MQTT network intrusion or anomaly detection, published 2024-2026, venue in the prereg list.
2. Reports uncertainty on a detection metric: CI, SE, error bar, +-, boxplot over runs, or a significance test.
3. Uses a public dataset. Record whether time order is recoverable (timestamp column, pcap, file order) — do NOT exclude if it is not; code `time_order_recoverable=0`.
4. Split type coded from the text: random | temporal | k-fold random | k-fold temporal | unclear.

## ci_method (one per claim)
iid_boot (bootstrap of test rows) | fold_t (t/normal over CV folds) | run_sd (SD over seeds/runs) |
wilcoxon (over folds/runs) | normal (binomial/normal on test rows) | none_but_claims_sig | other.
Dependence correction present? block/cluster bootstrap, ESS, HAC, batch means -> `dep_corrected=1`, else 0.

## Claim row (one per "A beats B" or per reported interval)
paper_id, venue, year, dataset, grain (packet|flow|window:s), split, metric,
metric_class (conditional: FPR/TPR/recall@FPR | prevalence_dependent: acc/F1/precision | rank: AUC/AUPRC),
model_a, model_b, est_a, est_b, se_a, se_b (derive from CI: (hi-lo)/(2*1.96) if normal-shaped), n_test,
ci_method, dep_corrected, data_released, code_released, time_order_recoverable, claim_text (verbatim, <=25 words).

## Decision rules
- If n_test is not stated, derive from dataset size x split fraction and code `n_test_derived=1`.
- If an interval is reported only graphically, read it with a plot digitiser and code `se_source=figure`.
- Summary-only claims are corrected by SE * sqrt(DIF_dataset,grain,family); released-data claims are
  recomputed with paired_difference_ci. Never mix the two in one table.
- Disagreements between coders are resolved by discussion and logged in corpus/disagreements.md.
