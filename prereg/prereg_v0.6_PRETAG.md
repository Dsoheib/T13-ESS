# Preregistration v0.6 — PRE-TAG (NOT yet frozen)

Freeze = `git tag prereg-v0.6`, HELD until: (a) n=20000 confirmation reproduces the factorial
pattern, (b) the five parents (Paxson-Floyd 1995, Kunsch 1989, Obuchowski 1997, Roberts 2017,
Arp 2022) are read in full (see docs/gate1_record.md), and (c) a valid H2 calibration exists on
>=1 time-order-audited flow dataset (the TON_IoT calibration is retracted; see
docs/calibration_findings.md and results/time_order_audit.csv). Simulation-only hypotheses
(SF-H4–H8) and SF-1 live in docs/simulation_findings.md, not here.

## Spine (P17 decision)
The reportable quantity is the **effective sample size n_eff**, not a confidence interval. A
dependence-*corrected interval* is claimed only where it demonstrably attains nominal coverage:
**FPR / alarm-rate under a short-memory benign background.** For recall and AUC the honest output
is n_eff (and, below the episode floor, the episode count), because no resampling restores
nominal coverage there. Working title reflects this:
*"Report the Effective Sample Size: Dependence-Inflated Intervals in Intrusion-Detection
Evaluation, and the One Metric You Can Still Correct."* (Abstract rewrite deferred until after
the tag.)

## Confirmatory hypotheses (thresholds fixed before any confirmatory-corpus run)

**H1 (prevalence).** Among IoT/IoMT NIDS papers (2024–2026, target venues) that use a time-aware
split AND report a CI/SE/error bar/significance test on a detection metric, the fraction that
corrects for within-test-set serial dependence is < 20 %. Void if > 50 %.

**H2 (inflation).** For each confirmatory-corpus benchmark **that passes the time-order audit**,
the benign-class DIF at the **flow grain** is >= 2. **Materiality is keyed to the conservative
within-minute-shuffle estimate (b)** — under minute-resolution timestamps (b) is the estimate and
the as-shipped row-order DIF (a) is an UPPER BOUND (P40); any DIF whose n_eff < 50 is reported as
not estimable, never as an interval. Material if median (b) DIF >= 1.5 with n_eff >= 50 on the
audited datasets.

**H2 STATUS (measured 2026-09-19, CICIDS2017 via HF mirror; audited):** SUPPORTED, feature- and
capture-dependent. Flow grain (b), benign, 3 days: median DIF **17.3** (all cells estimable),
timing/duration/size features 8–39; rate features (Flow Bytes/s) ~1 on benign Mon/Tue (Wednesday
inflated by the DoS block). Packet grain (true pcap order): inter-arrival DIF 23–75. Window grain
(AAL): median 96. **Finding (adopt): DIF is feature- and capture-dependent — there is no single
number per dataset; the DIF table is per-feature-per-grain, and this heterogeneity is itself the
reason the reporting requirement is needed.**

**H3a (interval-credibility — PRIMARY).** For each audited "A beats B" claim, compute n_eff and
DIF of the governing series and classify the reported interval as CREDIBLE or OVERSTATED at its
own n_eff. Headline = fraction of claims whose reported interval is not credible at n_eff.
Requires only the DIF, no nominal-coverage correction.

**H3b (restricted survival — SECONDARY).** Corrected-survival is computed ONLY for FPR/alarm-rate
claims on datasets that pass the time-order audit AND have demonstrably short-memory benign
background (DIF stable in n; Geyer/batch agree within 2x), via the paired block-bootstrap on
RELEASED data (`ci.paired_difference_ci`), block length from the loss-difference series. **The
summary-only sqrt(stream-DIF) SE-inflation arm is DROPPED on principle**: the Diebold-Mariano
loss-difference d_t = loss_A - loss_B has its own serial dependence, unrelated to either stream's
DIF, so inflating a reported SE by sqrt(stream DIF) is not justified.

**H3b EXPECTED OUTCOME (stated before computation, P42).** On calibration (CICIDS2017), the
BENIGN loss-difference DIF is ≈ 1.5 (estimable; the full-day ≈1860 value is a non-estimable
attack-regime artifact, n_eff≈40<50). SE widening = sqrt(1.5) ≈ 1.22. Therefore the expected H3b
result for FPR/alarm-rate A-vs-B claims is **HIGH SURVIVAL** — most such claims retain significance
after a ~22% SE widening. This is pre-registered as the expectation: H3b is expected to show that
FPR-type rankings are largely robust, and the paper's survival headline lives in H3a
(interval-credibility) and in recall/AUC where correction does not reach nominal, NOT in FPR
survival. Finding high FPR survival is confirmation, not a null result.

## Fixed analysis choices
- ESS: Geyer initial-positive-sequence (primary); batch-means reported alongside; a series whose
  Geyer and batch DIF differ by > 2x is FLAGGED and excluded from any headline number.
- DIF carries a segment CI (`dif_ci`); results with n_eff < 50 or < 10 resampled blocks are
  reported as "no interval; report n_eff", never as an interval.
- Estimand: threshold-conditional (charitable; see SF-1). Coverage dual-reported: non-computable
  counts as a miss (headline) + conditional + computability rate.
- Corrected interval: moving-block bootstrap (Kunsch), block = 2*tau_int of the slowest series;
  Politis-White as the reported alternative; Wilson-on-n_eff for the rare-event FPR.
- Confirmatory corpus datasets EXCLUDE the calibration datasets (TON_IoT-Fridge, TON_IoT-Weather).
- Time order declared UNRECOVERABLE / epoch-confounded where class∥time (e.g. TON_IoT as shipped);
  such datasets are reported, not silently corrected.
- Corpus venues/years and screening as in prereg_v1_DRAFT; survival counts descriptive (no
  multiplicity claim).

## Reliability of screening — AMENDED 2026-09-20 (P45; two-coder/κ clause withdrawn)
The original two-coder + Cohen's κ clause is UNSATISFIABLE and is replaced. No eligible second
coder exists: the supervisor co-authored the inclusion criteria and the H1 population definition
(agreement would measure shared provenance, not reliability); the agent is self-referential. The
author elects ONE of:

- **Option A (DEFAULT) — transparent single-coder screening.** Single coder screens; EVERY
  screened record is logged in `corpus/inclusion_log.csv` with decision, reason, and the exact
  criterion invoked; the full log + verbatim criteria ship with the artifact so any reader can
  re-screen. No κ is claimed.
  *Limitations text (if A):* "Inter-rater reliability was not established; a valid independent
  coder was unavailable. Screening reproducibility rests on the published inclusion log and the
  verbatim criteria, which permit any reader to re-screen the corpus."

- **Option B (author elects) — author-coded reliability subset.** The author independently codes a
  random 20 of the screened records, BLIND to the agent's decisions, against the verbatim criteria;
  κ is computed on that subset and reported; the agent codes the remainder. The B packet (random 20,
  verbatim criteria, `distribution_used` definition, blank coding sheet, no pre-filled judgements)
  is prepared in `corpus/B_packet/`.
  *Limitations text (if B):* "Inter-rater reliability was established on a random 20-record subset
  (κ = …); the remainder was single-coded against the same verbatim criteria."

Freeze applies whichever option the author elects; Limitations is set to match. Default A holds if
no election is made. **ELECTED: A (2026-09-20, revised).** Option B WITHDRAWN: no eligible
independent coder exists (supervisor co-designed the criteria; agent is self-referential), and per
P50/P62 the only kappa obtainable was on the abstract-screening PROXY, a stage superseded by
full-text confirmation -- an ornament that does not license the corpus. Author coding requirement
removed; the B packet (blank sheet, sealed decisions) is retired and its decisions are already in
inclusion_log.csv. Supervisor performs ADVERSARIAL REVIEW of the hardest screening decisions
(supervision, not reliability). Limitations text (A): "Inter-rater reliability was not established;
no eligible independent coder was available. Screening reproducibility rests on the published
inclusion log and the verbatim criteria (corpus/criteria.md); abstract-stage decisions are
superseded by full-text confirmation."

### B protocol (P46–P49, frozen before any reliability data exists)
- **P46 — frame size.** The random 20 is drawn from a screened frame of **>= 40** records
  (corpus/inclusion_log.csv has 44). Drawing 20 of 44 leaves >= 20 for the agent-only remainder,
  so the subset is a genuine sample, not the whole corpus.
- **P47 — blinding.** The agent's include/exclude decisions for the drawn 20 are WITHHELD from the
  author (sealed in corpus/B_packet/agent_decisions_SEALED.csv, committed separately BEFORE the
  author codes). The author receives only the blank coding sheet + verbatim criteria. The author's
  completed sheet is committed BEFORE the comparison; commit order (sealed-decisions commit, then
  author-sheet commit, then comparison commit) is the blinding audit trail.
- **P48 — adjudication.** κ is reported as computed on the blind subset (PRE-adjudication — that is
  the honest number). Disagreements are then adjudicated by discussion; adjudicated labels become
  final for those records. Criteria are revised ONLY if a disagreement reveals genuine ambiguity;
  any revision is logged in prereg/CHANGELOG.md and re-applied to ALL records, including those
  already screened.
- **P49 — κ floor.** Threshold fixed before computation: **κ >= 0.6 proceeds**; κ < 0.6 → criteria
  are revised and the subset is re-coded ONCE, then κ recomputed. The floor is preregistered; κ is
  not computed before the threshold is fixed.

## Deviations
Appended to prereg/CHANGELOG.md with date and reason after the tag.
