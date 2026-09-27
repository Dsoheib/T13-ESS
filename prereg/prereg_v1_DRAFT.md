# Preregistration — T1.3 (DRAFT, not yet frozen; freeze = git tag prereg-v1)

## Hypotheses (verbatim, thresholds fixed before any real-data run)
H1 (prevalence). Among IoT/IoMT NIDS papers (2024–2026, target venues) that use a time-aware
split AND report a confidence interval, standard error, error bar, or significance test on a
detection metric, the fraction that corrects for within-test-set serial dependence is < 20 %.
Materiality: headline holds if < 20 %; void if > 50 %.

H2 (inflation). For each public IoT IDS benchmark with recoverable time order, the
dependence-inflation factor DIF = n / n_eff of the benign-class score sequence at the flow
grain is >= 2. Materiality: >= 2 on at least half the datasets; void if median DIF < 1.5.

H3 (survival). After dependence correction, < 70 % of audited "A significantly beats B"
claims remain significant (non-overlapping intervals or p < 0.05). Materiality: 70 %;
if > 90 % survive, headline becomes "intervals anticonservative, rankings robust".

## Fixed analysis choices
- ESS truncation rule: Geyer initial positive sequence (primary); zero-crossing and Bartlett
  reported as sensitivity.
- Block length: 2 * tau_int of the slower of {label sequence, score sequence}, capped at n^(2/3).
- Primary corrected interval: moving-block bootstrap, B = 1000, percentile.
- Robustness: stationary bootstrap; ESS plug-in; block jackknife for AUC.
- Coverage simulation: scenarios iid / campaigns_only / dependent as in src/t13/sim.py,
  n = 20000, R = 500, B = 1000; must show naive < 85 % and corrected >= 90 % before real data.
- Corpus: venues {COSE, JNCA, TNSM, IoT-J, TIFS, USENIX Sec, CCS, NDSS} + volume stratum
  {Sensors, Electronics, Sci. Rep.}; years 2024–2026; inclusion = IoT/IoMT NIDS, reports
  uncertainty, public dataset with recoverable time order. Feasibility count logged in
  corpus/inclusion_log.csv before freeze.
- Datasets (candidates): CICIDS2017/2018, CICIoT2023, CICIoMT2024, MQTT-IoT-IDS2020 (pcap),
  MQTTset, TON_IoT, BoT-IoT (pcap), Edge-IIoTset, UNSW-NB15, MAWIFlow. Datasets shipped as
  shuffled CSV without timestamps are reported as "time order unrecoverable".
- Self-application: own V0 result and G24 censoring artefact, reported before corpus results.

## Deviations
Every deviation after the freeze is appended to prereg/CHANGELOG.md with date and reason.

## Added 2026-09-18 (v0.2 self-critique)
H4 (decomposition, preregistered because a pilot suggested it). Label-campaign dependence and
background autocorrelation degrade different metrics: campaigns break prevalence-dependent
metrics (accuracy, precision, F1); background autocorrelation breaks score-based metrics
(AUC, recall at fixed threshold). Test: coverage of naive intervals in campaigns_only vs
dependent scenarios; materiality = a coverage difference >= 0.30 between the two regimes
on the affected metric class.

H5 (episode floor). When a test window contains fewer than 10 attack episodes, no
resampling method (moving-block, stationary, episode/cluster bootstrap) restores nominal
coverage for recall; the reportable quantity is the episode count. Materiality: corrected
coverage < 0.85 whenever episodes < 10, at every n tested.

Fixed choices added:
- Block length = 2 * tau_int of the SLOWEST of {label sequence, score sequence(s)}, capped at n^(2/3).
- Interval type: 'basic' for bounded statistics (recall, AUC), percentile for others.
- Reliability: results with < 10 resampled blocks or n_eff < 50 are flagged, never reported as intervals.
- Long-range dependence: fGn scenario H in {0.7, 0.8, 0.9} added to the coverage simulation.
  Under LRD tau_int diverges with n; DIF is reported at the analysed n together with the
  batch-means estimate, and the paper states that DIF is n-dependent in that regime.
- Truth for coverage = population metric under the SAME threshold rule (threshold learned on
  the training half of a time-aware split) — the simulation now mirrors the field's protocol.
- Summary-only survival corrections (SE x sqrt(DIF)) are labelled first-order approximations and
  reported separately from released-data recomputations, which carry the headline survival number.

## Added 2026-09-18 (v0.3 self-critique)
H6 (random splits are uncorrectable). Under a random (shuffled) split, naive intervals on the
test set still fail to cover the population metric (shuffling hides dependence, it does not
remove it), AND no dependence correction can be applied because time order is destroyed.
Under a time-aware split the naive interval fails equally but the correction restores nominal
coverage. Materiality: corrected coverage >= 0.90 under temporal split and <= 0.80 under random
split for FPR, at every n tested.

Design statement: the coverage generator is STATIONARY (no drift), so point-estimate bias
between random and temporal splits is ~0 by construction. This isolates dependence from drift:
the temporal-bias/drift literature explains why estimates move; this paper explains why
intervals are wrong even when estimates do not move.

Fixed choices added:
- Block length: primary 2*tau_int (slowest series); Politis-White (2004) with Patton (2009)
  correction reported as the econometric alternative; the paper reports both.
- FPR at the operating point is the headline metric for the correction (class-conditional,
  prevalence-invariant, and the alarm-rate quantity operators budget); recall and AUC follow.
- DIF table per dataset reports three families: label, feature (full and benign-only), and
  reference detectors (IsolationForest, LogisticRegression, RandomForest) fitted with a temporal
  split; the alarm-indicator DIF at 1% FPR is the number that corrects published FPR intervals.
- Audit prevalence numbers carry Wilson intervals; two coders screen inclusion, Cohen's kappa
  reported; survival counts are descriptive (no multiplicity claim).
- Ordering sensitivity: flow start vs end time both reported where available.

## Added 2026-09-18 (v0.4 self-critique)
Estimand. Coverage is assessed against the THRESHOLD-CONDITIONAL truth (exact under the generator):
the quantity a test-set interval claims to cover is the detector's FPR / recall at the learned operating
point. Unconditional and window-conditional truths are reported to show the size of the conflation error.
H7 (effective-epoch floor). When n_eff = n/DIF < 50 on the relevant series, no resampling method attains
coverage >= 0.85; the reportable output is n_eff. Materiality: holds at every n and scenario tested.
Long-range dependence is a declared limitation: corrections at fixed block length under-cover for H >= 0.8;
the subsampling rate 1-H route is future work; the batch-means DIF is reported as a scale-dependent descriptor.
Prereg simulation settings: n_test = 20000, R = 500, B = 1000; scenarios iid, campaigns_only, dependent,
lrd_H0.7, lrd_H0.8; splits temporal and random.

## Added 2026-09-18 (v0.5 self-critique)
- DIF carries its own block-bootstrap interval (dif_ci); the audit's corrected SEs are reported with
  the DIF interval propagated (sensitivity band), not as a point correction.
- Estimator agreement: a series whose Geyer and batch-means DIF differ by > 2x is flagged; flagged
  series are reported but excluded from the headline survival count.
- FPR intervals use Wilson with n_eff (rare-event proportion), not the normal ESS plug-in.
- Heavy-tailed background (Student-t3 innovations) added to the coverage scenarios.
- DIF-estimator study (relative bias and SD of each rule vs n and tau) is a reported table, run at
  R = 200 per cell; pilot: Geyer unbiased with relative SD 0.04-0.33; batch-means biased low (-0.06 to
  -0.66) when n_eff < 100; Bartlett unusable (-0.9) under strong dependence.
- Floor curve (F3): coverage vs n_eff for FPR and AUC; pilot at n_eff ~ 146: FPR ESS/MBB 0.95 vs naive
  0.75; AUC MBB(PW) 0.80 -> AUC residual anticonservativeness is a declared limitation (H8: after
  correction AUC coverage stays below 0.90 whenever the window holds < 20 attack episodes).

## Added 2026-09-19 (post-diagnosis reconciliation; supersedes conflicting items above)

Context: external review REJECTed the first coverage run. Diagnosis (diagnostics/) established
that the earlier "control failure" was an ESTIMAND mismatch, not a dependence effect, and that
the correction is more modest than claimed. This section rescopes the prereg accordingly. Still
a DRAFT; freeze = git tag `prereg-v1` after the n=20000 confirmation run.

**Charitable-estimand declaration (goes in the claim and abstract).** All dependence-miscoverage
is measured against the threshold-conditional estimand — the estimand most favourable to the
audited authors, since it excludes the threshold-estimation gap of SF-1 (see
docs/simulation_findings.md). Published intervals are audited under the estimand that gives them
their best possible coverage, and they still fail under dependence.

**Dual coverage reporting (P9).** Every coverage number is reported two ways: (a) counting
non-computable intervals as failures (headline), and (b) conditional on computability with the
computability rate beside it. No cell with computability < 1 is reported single-figure.

**H3 rescope — DECISION: convert to an interval-credibility count (primary); FPR-survival as a
restricted secondary.** A survival audit requires a correction with demonstrated nominal
coverage; post-diagnosis we have that only for FPR under short-memory background. Therefore:
- H3a (primary, interval-credibility): for each audited "A beats B" claim, report n_eff and DIF
  of the governing series and classify the reported interval as CREDIBLE / OVERSTATED given the
  dataset's DIF; the headline is the fraction of claims whose reported interval is not credible
  at its own n_eff. This needs no nominal-coverage correction, only the DIF.
- H3b (secondary, restricted survival): the corrected-survival rate is computed ONLY for
  FPR/alarm-rate claims on datasets whose benign background is short-memory (DIF stable in n,
  Geyer/batch agreement within 2x); recall/AUC claims are reported as "no validated correction"
  rather than given a survival verdict.
This determines claims.csv: it must extract metric_class (conditional / prevalence-dependent /
rank), the reported interval/SE, n_test, data_released, AND enough to map the claim to the
governing series' DIF.

**H4 decomposition now uses the factorial (P11).** The single `dependent` scenario is replaced
by the 2x2 {background: iid, AR(0.9)} x {labels: scattered, campaign} (src/t13/sim.py FACTORIAL).
H4 materiality is restated: FPR/AUC coverage is degraded by the background factor and ~unaffected
by the label factor; recall coverage is degraded by both. Test on the four factorial cells.

**Simulation settings actually run (post-diagnosis):** n_test = 5000, R = 500 (control iid at
R = 1000 for MC SE <= 0.01), B = 200, seed 0, estimand = threshold-conditional, FPR = Wilson.
The prereg confirmation run at n = 20000, R = 500, B = 1000 remains REQUIRED before freeze.

**H6 (random vs temporal) is under test at the corrected estimand;** if temporal-corrected does
not exceed random-corrected for FPR with non-overlapping MC SE, H6 is WITHDRAWN (the marginal
metric is estimable from a shuffled sample, so random-split naive may cover the conditional
truth — a nuance the original H6 did not anticipate).
