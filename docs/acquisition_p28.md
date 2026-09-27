# Acquisition + P28 as a release-practice claim (revised 2026-09-19)

**Correction of the prior version.** The earlier claim "no time-ordered flow dataset is openly
obtainable" was WRONG — it rested on one redirect chain without checking mirrors or the network
allowlist. CICIDS2017 GeneratedLabelledFlows.zip (with `Timestamp`) is openly mirrored on Hugging
Face (`bencorn/CICIDS2017`, host reachable here), was downloaded (283,876,488 bytes), unzipped,
and audited. H2 is now MEASURED. The finding below is reframed as a claim about release PRACTICE
(verifiable in the corpus), not about availability (falsifiable by one mirror).

## Per-host acquisition outcome
| host | reachable | carries CICIDS2017 ordered flows? | outcome |
|---|---|---|---|
| huggingface.co / us.aws.cdn.hf.co | YES (200) | yes: csvs/GeneratedLabelledFlows.zip + 5 daily pcaps | **DOWNLOADED GeneratedLabelledFlows.zip** |
| 205.174.165.80 / cicresearch.ca (CIC server) | reachable | gated: 301→302→unb.ca/cic/datasets/index.html | citation-request page (not an approval gate; the files are stated public) |
| github.com / raw.githubusercontent.com | YES | mirrors exist (MachineLearningCVE variants) | not needed |

No x-deny-reason was hit; huggingface.co was reachable despite not being an assumed allowlist host.

## The finding, restated as release practice (P33)
The ordered form EXISTS and is obtainable. What the field does with it is the finding:
1. **CICIDS2017 GeneratedLabelledFlows** ships a `Timestamp` and flows in capture (row) order —
   ORDER RECOVERABLE (0 duplicate rows). Caveat: the Timestamp is minute-resolution
   (unique_ts_frac 0.0009), so within-minute order needs the row order, and afternoon times are
   12h without AM/PM — a documented integrity wrinkle, but the sequence is recoverable.
2. **CICIDS2017 MachineLearningCVE** — the release most IDS papers actually use — **drops the
   Timestamp**. Order is unrecoverable in the form the corpus consumes.
3. **MAWIFlow** public v1.0.0 release is RANDOM stratified balanced samples (sampler.py) →
   adjacency destroyed; the ordered Parquet is behind a DVC remote not in the public repo.
4. **TON_IoT** on disk: 68% Δt≤0, 3:1 timestamp collisions, 17%/4% duplicate rows — unrecoverable.
5. **CICIoMT2024** on disk: no timestamp column — unrecoverable.

**Claim:** the ordered form of the field's most-used flow benchmark exists, but the derivative the
field predominantly evaluates on (MachineLearningCVE; balanced samples) is order-destroyed. With
SF-H6 (a random split hides residual dependence: seen τ̂ 1.04 vs true 10.27), the practical result
is that most published intervals on these benchmarks were computed on a form from which the
dependence signal had already been removed — so they are uncorrectable by the reader in the form
used, even though an orderable release exists. This is a claim about PRACTICE, to be quantified in
the corpus via the new `distribution_used` field, not a claim about availability.

## H2 verdict (P29 decided)
Measured on genuine, time-order-audited data:
- **Flow grain (CICIDS2017-Wed, 150k):** benign-feature median DIF = **26.0**, 6/7 features ≥ 2,
  Geyer/batch agreeing on the headline features. **H2 SUPPORTED at flow grain** — flow aggregation
  does NOT absorb the dependence.
- **Window grain (AAL MQTT bridge, §3.4):** benign-feature median DIF = **96**, 15/16 ≥ 2
  (conservative reliable-agreeing subset still 2–25).
- **Packet grain:** requires the daily pcap (available on the same HF mirror); parsing deferred —
  reported as pending, not a blocker.

H2 is the "paper in the plan" outcome: the per-dataset DIF table is the reusable artifact, and
H3a/H3b run. Not the DIF≈1 collapse outcome.
