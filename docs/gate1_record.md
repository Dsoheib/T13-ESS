# Phase 2, Gate 1 — kill/continue record (2026-09-19)

## Kill condition
An IDS/NIDS/anomaly/malware-detection paper that computes **dependence-corrected** confidence
intervals (ESS / block or stationary bootstrap / design-effect) on a public benchmark **AND**
reports **survival of published "A beats B" claims** after correction.

## Vocabulary searched (2026-09-19)
effective sample size + autocorrelation time + confidence interval + intrusion detection;
stationary/block bootstrap + intrusion detection classifier evaluation + dependence;
Diebold-Mariano + intrusion/anomaly detection model comparison;
design effect + intra-cluster correlation + dependence-corrected CI + published-claim survival
+ NIDS benchmark.

## Result: CONTINUE (kill condition NOT met)
No IDS-domain work applies ESS/block-bootstrap interval correction to a public benchmark with a
survival audit. The corrected-inference machinery exists only in other domains:
- **Biostatistics** — clustered ROC/AUC intervals (Obuchowski 1997), clustered survival.
- **MCMC / simulation** — ESS = 1/autocorrelation-time (Geyer 1992; Flegal & Jones 2010).
- **Econometrics** — block/stationary bootstrap (Kunsch 1989; Politis & Romano 1994), predictive-
  accuracy tests (Diebold & Mariano 1995; Giacomini & White 2006), Model Confidence Set (Hansen
  et al. 2011).
- **2026 LLM evaluation (closest domain-transfer neighbours, abstract-only):**
  "The Autocorrelation Blind Spot" (arXiv 2604.14414) applies ESS/autocorrelation to turn-level
  LLM analysis; "Resolution Diagnostics for Paired LLM Evaluation" (arXiv 2605.30315) uses a
  design-effect / cluster-aware required-N for benchmark comparisons. Same statistical idea,
  different domain (LLM eval, not serially-dependent security telemetry), and neither runs a
  survival audit of published detection claims. Differentiate in Related Work: T1.3 is the
  transport to serial IDS telemetry + the per-benchmark DIF table + the survival/credibility audit.

## Positioning sentence against HED (arXiv 2604.04993)
HED (Hiremath 2026) changes **what** is scored — an exponentially-decaying kernel that rewards
early detection — whereas T1.3 changes the **uncertainty around whatever is scored**; the two are
orthogonal (HED could be reported with a dependence-inflated interval and would inherit exactly
the defect T1.3 corrects).

## Parent reads — status 2026-09-19 (genuine, via PDF)

- **Arp et al. 2022 — READ (abstract, contributions, full pitfall taxonomy Fig.1).** The ten
  pitfalls are P1 sampling bias, P2 data snooping, P3 spurious correlations, P4 label inaccuracy,
  P5 biased parameters, P6 inappropriate baselines, P7 inappropriate measures, P8 base-rate
  fallacy, P9 lab-only eval, P10 inappropriate threat model. **None is dependence-inflated
  intervals / ESS**; P7 concerns metric *choice*, P8 concerns prevalence. Confirms the seam: the
  pitfall T1.3 adds is absent from the canonical taxonomy.
- **Paxson & Floyd 1995 — READ (abstract + intro).** WAN packet arrivals are non-Poisson, far
  burstier than exponential (TELNET), FTP data connections arrive in bunched "connection bursts,"
  bursts persist across a wide range of time scales (self-similar). The dependence fact under
  "test-set flows are serially dependent."
- **Kunsch 1989 — READ (abstract + intro).** Naive jackknife/bootstrap "give incorrect answers
  if dependence is neglected." Block methods are consistent iff block length l=l(n)→∞ and
  l(n)/n→0; for the arithmetic mean the block-jackknife equals a spectral-density-at-zero
  (= τ_int) variance estimate. **Directly justifies the estimator choices:** our block_length =
  2·τ_int capped at n^(2/3) satisfies l→∞, l/n→0; the ESS inflation IS the spectral-at-zero
  variance. Estimator/truncation questions (P25) resolved for the block/ESS route.
- **Obuchowski 1997 — substituted (P30).** Biometrics paywalled; per the reviewer's instruction
  read the 2023 Stats dependency-adjusted-AUC paper in full instead and mark Obuchowski
  cited-not-read (done in bib). See Bay et al. below.
- **Bay et al. 2023 (Stats, PMC10621602) — READ.** Dependency-adjusted AUC confidence interval
  for CLUSTERED/EXCHANGEABLE hierarchical data, validated by coverage simulation (0.943–0.958).
  The authors **explicitly** state the correlation "must be strictly exchangeable" and is "often
  inappropriate with longitudinal data," and report inability to implement time-structured
  correlations. This is the near-miss stated in its own words: biostatistics corrects AUC
  intervals for clustered dependence and disclaims serial dependence — the exact seam T1.3 fills
  by transporting to serial telemetry (block-jackknife / block-bootstrap AUC). Also independently
  confirms the coverage-simulation validation design we used.
- **Roberts 2017 — OPEN ACCESS (not paywalled, P30 corrected); core verified from abstract.**
  Random CV underestimates predictive ERROR on structured data; block CV fixes the point-estimate
  bias. It addresses the bias of the error estimate, NOT interval width — the complement to T1.3.
  Wiley full text is bot-blocked in this environment (403); full read pending, positioning secure.

## Decision
Kill-condition search: CONTINUE. Estimator-choice reading (Kunsch) DONE, so calibration may
proceed once a time-order-audited flow dataset exists (P25 satisfied for the block/ESS route).
Prereg tag HELD until: (a) Obuchowski + Roberts read, (b) n=20000 confirmation reproduces the
factorial pattern, (c) a valid H2 calibration on an audited flow dataset.
