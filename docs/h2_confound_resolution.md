# H2 confound resolution: P35 (order), P37 (multi-day), P36 (differential) — 2026-09-19

Instrument frozen at `sim-frozen`. CICIDS2017 GeneratedLabelledFlows (HF mirror), benign flows,
cap 67k/day. `results/p35_order_confound.csv`.

## P35 — is the flow-grain DIF serial, clustered, or a sub-minute ordering artifact?
Three-way per feature: (a) as-shipped row order; (b) within-minute order randomised, R=20;
(c) five-tuple deduplicated (first flow per Flow ID). Wednesday:

| feature | (a) row | (b) min-shuffle ±sd | (c) dedup5tuple |
|---|---|---|---|
| Flow Duration | 62.7 | 37.7 ±3.1 | 66.9 |
| Flow Bytes/s | 62.9 | 63.9 ±0.4 | 102.8 |
| Flow Packets/s | 26.0 | 31.5 ±0.5 | 118.1 |
| Flow IAT Mean | 17.1 | 21.2 ±1.9 | 41.7 |
| Bwd Pkt Len Mean | 17.3 | 15.2 ±0.7 | 93.2 |

**Verdict: genuine SERIAL dependence.** (b) does not collapse → not a sub-minute ordering
artifact (dependence lives across minutes). (c) does not collapse (rises) → not five-tuple
clustering. Parent stays **Künsch (serial)**, not Obuchowski (clustered). Both confounds ruled out.

## P37 — multi-day, incl. Monday (benign-only clean test)

| feature | Mon (benign-only) a/b/c | Tue a/b/c | Wed a/b/c |
|---|---|---|---|
| Flow Duration | 43.5 / 28.2 / 44.1 | 61.0 / 12.5 / 67.6 | 62.7 / 37.7 / 66.9 |
| Flow Bytes/s | **1.1 / 1.0 / 8.0** | **1.1 / 1.0 / 1.6** | 62.9 / 63.9 / 102.8 |
| Flow Packets/s | 5.7 / 6.1 / 4.6 | 5.5 / 9.9 / 3.8 | 26.0 / 31.5 / 118.1 |
| Flow IAT Mean | 12.0 / 18.5 / 14.5 | 6.4 / 8.3 / 9.2 | 17.1 / 21.2 / 41.7 |
| Bwd Pkt Len Mean | 44.9 / 38.9 / 15.4 | 13.6 / 17.5 / 14.7 | 17.3 / 15.2 / 93.2 |

**Findings:**
- Serial dependence is real and confound-robust for **timing/duration/size** features on ALL
  three days including clean benign-only Monday (Flow Duration 43/61/63; Flow IAT 6–17; Bwd Pkt
  Len 14–45) — H2 is NOT a one-day/attack-block artifact.
- It is **feature-dependent:** Flow Bytes/s is ~iid on benign Monday/Tuesday (DIF 1.1) and only
  large on Wednesday — the Wednesday value was inflated by the contiguous DoS-Hulk block. Rate
  features can be ~1; the dependence lives in timing/duration/size.
- Honest H2 magnitude on clean background ≈ 10–45 (dependent features), median well above 2;
  Wednesday's 63–96 headline over-states (P37 confirmed). Report per-feature, not a single number.

## P36 — differential DIF diagnosed (variance + τ of the difference series, Wednesday)

| pair | mean_diff | var_diff | τ (=DIF) |
|---|---|---|---|
| iforest-logreg | 0.0007 | 0.00145 | 5.4 |
| iforest-rf | 0.216 | 0.170 | 1859 |
| logreg-rf | 0.216 | 0.170 | 1869 |

**Not a small-denominator artifact** (the ~1860 pairs have the LARGEST variance, 0.17). The τ=1859
is genuine strong serial dependence in the loss-difference: rf systematically differs from
iforest/logreg over the contiguous DoS-Hulk block (mean offset 0.22, long low-frequency
structure). So "A-vs-B SE is dependence-inflated" DOES follow — but the magnitude is regime-driven
(attack block), the same P37 caveat; on clean background it would be smaller. The stream/differential
divergence is real → sqrt(stream-DIF) SE inflation invalid (H3b summary-only arm stays dropped);
the paired block bootstrap on released data is the correct route.

## Packet grain — true sub-second order from the PCAP (definitive P35, no ordering ambiguity)
Range-downloaded the first ~400 MB of the Wednesday pcap (HF mirror), parsed with tshark:
322,875 benign packets over 244 s, in true capture order (pcap timestamps = ground truth).

| series (true pcap order) | DIF_geyer | DIF_batch |
|---|---|---|
| inter_arrival_time | **75.3** | 23.3 |
| packets_per_1s | 56.2 | 14.3 |
| packet_size | 1.1 | 10.5 (Geyer/batch disagree -> long-range, flagged) |

Packet inter-arrivals and per-second rates are strongly serially dependent at the finest grain
where NO ordering ambiguity is possible — the direct measurement of Paxson & Floyd's bursty /
self-similar arrivals. This is the definitive resolution of P35: the dependence is real, not an
artifact of flow-record ordering.

## (b) vs (a) diagnosis (P43) — (a) is NOT a universal upper bound
Correction of an earlier overclaim. Row-order Flow IAT Mean has POSITIVE short-lag acf
(rho1 = 0.18/0.19/0.14 Mon/Tue/Wed), yet (b) within-minute-shuffle > (a) row order for that feature
(Mon 18.5>12.0, Tue 8.5>6.4). Mechanism (one sentence): within-minute shuffling replaces the
within-minute autocorrelation *decay* with a flat *plateau* at the minute-level (block-mean)
correlation, so the Geyer initial-positive sum runs longer and (b) EXCEEDS (a) for features whose
dependence sits at the minute scale (Flow IAT Mean), while it falls BELOW (a) for features whose
dependence is within-minute (Flow Duration, Bwd Pkt Len). **Per-cell bounding:** (a) bounds (b)
from above only where (a) >= (b) — true for Flow Duration and Bwd Pkt Len on all days, FALSE for
Flow IAT Mean (Mon, Tue) and some Flow Packets/s cells. So (a) is neither a universal per-cell
bound nor a bound on the median; **(b) is the reported estimate per cell, with (a) shown beside
it**, and the headline uses (b).

## Packet grain — 3 NON-ADJACENT windows across ~5h (P41), pcapng resync
The capture is pcapng; resync on Enhanced Packet Blocks. Three byte-range chunks (early/mid/late),
epochs 1499255312 / 1499256537 / 1499273216 (span ~5h). n_eff and window length per row:

| window | len | series | DIF geyer/batch | n_eff | note |
|---|---|---|---|---|---|
| early | 21 s | inter_arrival | 2.1 / 1.8 | 43576 | well-powered; genuinely low in this window |
| early | 21 s | packet_size | 1.0 / 1.0 | 89696 | well-powered; low |
| early | 21 s | packets/1s | 1.0 / 1.0 | **22** | **UNDERPOWERED** (21 one-sec points): not evidence of absence |
| mid | 203 s | inter_arrival | 163.4 / 26.9 | 481 | strong |
| mid | 203 s | packet_size | 1505 / 52 | 52 | Geyer/batch DISAGREE >2x → FLAGGED not-estimable |
| mid | 203 s | packets/1s | 4.7 / 4.6 | 43 | underpowered |
| late | 128 s | inter_arrival | 152.0 / 16.5 | 190 | strong |
| late | 128 s | packet_size | 222 / 37 | 130 | Geyer/batch DISAGREE → FLAGGED |
| late | 128 s | packets/1s | 5.8 / 5.9 | 22 | underpowered |

**Inter-arrival DIF ranges 2 → 163 across windows** — capture-dependent, not one stationary value.
Per P44: the early inter-arrival window is WELL-POWERED (n_eff 43576) so its low DIF (2.1) is a
genuine per-window value, not a power artifact; but the per-second series (n_eff 22) is underpowered
everywhere (short windows) — a low DIF there is not evidence of absence. packet_size is flagged
not-estimable in the dependent windows.

## FINDING (adopt): DIF is feature- AND capture-dependent — no single number per dataset
Across grains and captures the DIF spans ~1 to ~160+ depending on feature, day, and capture window
(Flow Bytes/s ~1 on benign Mon/Tue vs 64 on Wed; inter-arrival 2 vs 163 across windows). This
heterogeneity is a result, not noise: it is precisely why the paper's reporting requirement (report
n_eff and DIF per metric, per grain, with the estimator-agreement flag) is necessary. A single
"dataset DIF" is not a well-defined quantity.

## Net H2 status — SUPPORTED, heterogeneous, on genuine confound-controlled data
- **Flow grain (CICIDS, conservative (b) estimate, 3 days incl. clean Monday):** median DIF 17.3,
  timing/size features 8–39, all estimable; rate features ~1 (feature-dependent). (a) row order is
  an upper bound only (minute-resolution timestamps).
- **Packet grain (true pcapng order, 3 windows):** inter-arrival DIF 2–163 (capture-dependent);
  packet_size flagged not-estimable.
- **Window grain (AAL MQTT bridge, not subject to P35):** median DIF 96 — the anchor.

## H2 restated under the estimator-agreement rule (P99, 2026-09-22)

H2 = "flow/window aggregation does not absorb the serial dependence (benign DIF stays >= 2)."
Restated with the rule applied UNIFORMLY (non-deterministic; Geyer/batch within 2x; n_eff >= 50;
failing (ii) -> estimator range, failing (iii) -> not estimable). Source: results/dif_headline.csv.

- **Flow grain (CICIDS2017-Wed, public benchmark) — H2 SUPPORTED, and now the primary evidence.**
  5/7 benign features qualify (as-shipped order): Flow Duration 63.5, Total Fwd Packets 1.0,
  Flow Bytes/s 62.7, Flow Packets/s 26.0, Bwd Packet Length Mean 17.3; median 26.0. Two features
  (Flow IAT Mean, Fwd Packet Length Mean) are estimator ranges. The within-minute-shuffle (b)
  headline median is 17 (conservative). Both medians are far above 2.
- **Packet grain (CICIDS pcap) — supported where estimable.** Early inter-arrival qualifies at 2.1;
  mid/late inter-arrival are estimator ranges (Geyer 152-163 vs batch 16-27) under long-range
  dependence; per-second not estimable; packet size flagged.
- **Window grain (AAL, owned) — CORROBORATION, not the anchor.** After excluding time_sin/time_cos
  (deterministic clock encodings) and the series failing the rule or the n_eff floor, 3 features
  qualify: regularity_coefficient 1.96, temporal_clustering_score 3.51, normal_emergency_ratio 6.26;
  median 3.5. The all-feature median 96 was dominated by flagged/not-estimable series and is no
  longer a headline.

**Verdict:** H2 holds — aggregation does not absorb the dependence — but the empirical weight moves
to the public CICIDS2017 flow grain; the AAL window result is corroboration (median 3.5, still
above 2), not the anchor. The earlier "window median 96" was a median over mostly flagged series and
is withdrawn as a headline.
