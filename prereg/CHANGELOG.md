# Deviations log (append-only)
- 2026-09-18  repo created; prereg v1 drafted, NOT frozen.
- 2026-09-18  pilot simulation (n=6000, R=100, B=200) run for code validation only; results
  not to be reported. Observation: block length must follow the slower dependence structure
  (campaign length vs background); to be fixed in prereg before freeze.
- 2026-09-18  v0.2: self-critique pass. Added batch-means and AR(1) ESS rules, reliability flags,
  slowest-series block length, basic intervals, episode bootstrap, fGn (LRD) scenario, time-aware
  split with learned threshold in the simulation, real-data DIF pipeline (datasets.py), 10 tests.
  Fixed: block length previously followed the score series only; aggregation dtype bug in run().
  Pilot (n_test=5000, R=80, B=150; validation only): naive coverage 8-18% for accuracy and 35-44%
  for recall/AUC under dependence; corrected 84-92% (accuracy), 67-71% (recall), 57-81% (AUC).
  Episode bootstrap collapses below ~10 episodes -> H5.
- 2026-09-18  v0.3: Politis-White block length; FPR-at-threshold metric; Wilson interval; random-vs-
  temporal split variant with point-estimate bias; reference-detector DIF (iforest/logreg/rf) and
  clean windowing in datasets.py; F2 (2x2) script; 14 tests incl. iid-coverage regression guard;
  requirements/LICENSE/CITATION. Pilot 2x2 (dependent, n=4000, R=50): random split -> naive FPR
  coverage 74%, uncorrectable (72%); temporal split -> naive 58%, corrected 92-96%. Bias ~0 both.
- 2026-09-18  v0.4: estimand fixed to threshold-conditional truth (a test-set interval conditions on the
  learned operating point); window-conditional and unconditional truths also reported. Subsampling CI,
  Politis-White AUC variant, vectorised stationary bootstrap, CODEBOOK.md, CIC adapter, Makefile targets,
  bib additions (Dehling-Wendler for AUC validity; Politis-Romano-Wolf; Hall-Jing-Lahiri for LRD).
  Finding: at n=5000 the 'dependent' scenario has n_eff~20 -> NO method covers (effective-epoch floor);
  at n=20000 conditional-truth FPR coverage: naive 50%, ESS/MBB 90% (R=30). LRD H=0.8: corrections at
  fixed L fail (45-67%) -> stated limitation, not tuned away.
- 2026-09-18  v0.5: Wilson-with-ESS FPR interval; DIF bootstrap interval; Geyer/batch agreement flag;
  heavy-tail scenario; DIF-estimator study + floor curve (F3) scripts; survival CLI keyed by
  (dataset, grain, metric_class); make_tables.py so paper numbers are never hand-typed; .gitignore.
  Pilot findings recorded in prereg v0.5 section. 16 tests.

## 2026-09-20 — Option B elected; B packet drawn; prereg FROZEN (tag prereg-v1)
- Reliability clause amended (P45): two-coder/kappa withdrawn; Option B elected. P46-P49 added
  (frame>=40, blinding, adjudication, kappa floor 0.6).
- Random-20 drawn from 43-record frame, SEED=20260920. Agent decisions sealed
  (corpus/B_packet/agent_decisions_SEALED.csv), committed before author coding.
- H3b expected outcome stated before computation (high FPR survival). Flow-grain keyed to (b).
- Prereg frozen at this commit and tagged prereg-v1 BEFORE the author codes, so the kappa floor
  is a genuine preregistered threshold.

## 2026-09-20 — P50 scope clarification (NOT a deviation; criteria unchanged)
Title/abstract screening cannot reliably determine `time_aware_split` or `reports_ci_or_test`
(the two fields H1 turns on). Therefore: the 44-record log is a CANDIDATE POOL, not a final
screened corpus; final inclusion is FULL-TEXT confirmed. Cohen's kappa (Option B) is reported on
the ABSTRACT-SCREENING stage (agreement on the proxy the abstract supports), explicitly labelled
as such; final inclusion kappa is not claimed at this stage. Coders mark `unclear` when the
abstract is insufficient (guessing from the same weak signal would inflate kappa). The prereg
inclusion criteria are UNCHANGED — this records what the kappa measures, not a change to the rule.

## 2026-09-20 — P52 arXiv / preprint status rule (decided, applied uniformly)
The venue frame does not name arXiv. RULE: arXiv and other preprints (incl. preprints.org
`hidden2026variable`) are IN the VOLUME stratum, flagged `preprint`, and reported as a distinct
sub-stratum. If a preprint also appears in a frame venue, the published version supersedes and the
preprint row is dropped. H1 is reported three ways for sensitivity: (core), (core + published
volume), (all incl. preprints). Applied uniformly to all pool records; preprint rows marked in
inclusion_log `stratum`.

## 2026-09-20 — P53-P56 (post-freeze, agent parallel; criteria unchanged)
- H3a schema rewritten (docs/h3a_schema.md): n_eff PRIMARY, continuous k=sqrt(DIF) reporting,
  ordinal bands DROPPED (no threshold set from observed magnitudes, P54). dif_used is a RANGE keyed
  to (dataset,grain,feature-class) with a most-specific-first matching rule; conservative end is the
  lower bound (P55). NOT-ASSESSABLE (order-destroyed release or n_eff<50) kept as its own headline.
- P56: direct publisher-DB enumeration via web search FAILS (returns arXiv mirrors; IEEE Xplore /
  ScienceDirect abstracts not indexed even with domain filter). Core-stratum thinness is partly a
  search-method artifact. Pooled-corpus H1 framing adopted PROVISIONALLY; core enumeration to be
  redone via ISCC institutional database access (author) before the sharp claim is demoted for good.
  Two core leads added (TIFS self-supervised 2024; ScienceDirect IoMT ensemble) -> core ~10.

## 2026-09-20 — P59/P60 H1 framing correction (reading of frozen criteria; NOT a deviation)
1. H1 population is PRACTICE-DEFINED (frozen prereg-v1): papers using a time-aware split AND
   reporting a CI/SE/error-bar/significance test. VENUE is a reporting STRATUM, not the denominator.
   A Sensors paper with a chronological split + 95% CI is a full member; a TIFS paper with a random
   split is not. The prior pooled-fallback / core-count demotion is WITHDRAWN. Frozen criteria
   unchanged — this records the correct reading.
2. H1 reporting form: headline runs against the TIME-AWARE subset across the FULL pool; venue
   stratification (core / published-volume / preprint) reported BESIDE it as a descriptive
   breakdown, never as a filter on the denominator.
3. P56 trigger (preregistered now, before the subset size is known): IF full-text screening finds
   the time-aware subset contains ZERO core-venue records, THEN one focused hour of IEEE Xplore +
   ScienceDirect queries targeted at time-aware-split IDS in IoT-J / TIFS / C&S is warranted.
   Otherwise no database work. ISCC-access dependency withdrawn.
4. Declared risk (recorded pre-hoc): if the time-aware subset is < ~5 papers, no framing rescues
   H1; the audit arm reduces to H3a credibility + the release-practice (NOT-ASSESSABLE) finding.
   The instrument, the three-grain DIF table (AAL anchor), SF-1, the episode floor, and SF-H6 carry
   the paper regardless.

## 2026-09-20 — P61/P62/P63: criteria repaired; Option A elected; B withdrawn
- P61: corpus/B_packet/criteria.md criterion 2 contained an en-dash "2024–2026" (U+2013) that
  corrupted downstream (rendered "not still"). REPAIRED: canonical corpus/criteria.md is ASCII-only
  ("2024 to 2026"), diffed criterion-by-criterion against prereg-v1 (intent identical; P52 preprint
  clause added). B_packet retired.
- P62/P63: kappa gate REMOVED. Its value collapsed at P50 (abstract stage can't resolve the two
  decisive fields; superseded by full-text) and no eligible second coder exists. Reliability clause
  = Option A (single-coder, full log + verbatim criteria shipped, no kappa). Election, not a
  deviation (A was the prereg default). Supervisor does adversarial review of the hardest decisions.
- agent_decisions_SEALED.csv unsealed: decisions already present in inclusion_log.csv; blinding
  served nothing once B was withdrawn.

## 2026-09-20 — H1 RETIRED (P68/P71); corpus demoted; SF-2 scaled
- H1 (prevalence: fraction of time-aware+uncertainty papers correcting for dependence) is RETIRED
  -- NOT void, NOT measured: insufficient RESOLVABLE denominator. In-frame full-text resolution
  reached 5/16 = 31% via open access (60% target unmet; remainder access-blocked: IEEE Xplore,
  ScienceDirect, MDPI-403, Nature-auth). A prereg hypothesis that cannot be measured at the
  available resolution is reported as retired-for-access, with the rate on record, not dropped.
- Corpus DEMOTED (P68): no longer an audit/contribution; it is an ILLUSTRATIVE SAMPLE supporting
  the reporting requirement, n and access ceiling stated in the opening sentences, no prevalence
  language. Proceeding on NO institutional access (access question closed).
- SF-2 promoted: scaled corpus coding of uncertainty_kind (target n>=30) + SF-2 simulation
  (diagnostics/sf2_seed_vs_testset.py) run against sim-frozen (additive; frozen modules untouched).
- 2026-09-22  DEVIATION (bootstrap replicates B). The prereg fixes the coverage simulation at
  n=20000, R=500, B=1000. The canonical reported run (results/coverage_sim.csv, Table 1) used
  n=5000, R=500, B=200; the n=20000 confirmation run of record (coverage_sim_n20000.csv,
  split_2x2_n20000.csv, Table 2) used B=150. REASON: runtime -- per-replicate cost is ~1.15 s at
  n=20000/B=200 (docs/runtime_audit.md), so the full factorial at B=1000 is ~6-7 h; the bootstrap
  cost is linear in B. IMPACT: the reported FPR intervals are Wilson-on-n_eff and the reported
  recall intervals are naive-normal / ESS plug-in -- none contains a bootstrap, so the headline
  FPR coverages (incl. the 0.948/0.714 split result) are B-independent by construction. Only the
  AUC columns (naiveBoot, mbb) depend on B. SENSITIVITY: the MBB-dependent factorial cells were
  re-run at B=1000 (scripts/sensitivity_B1000.py -> results/coverage_sim_B1000.csv) and compared
  to B=200 against combined MC SE; result recorded in docs/n20000_confirmation.md and, as one line,
  in the paper's Limitations. sim-frozen and prereg-v1 untouched (additive script only).
- 2026-09-22  P102: the B=1000 sensitivity was run at n=5000 (full factorial, scripts/sensitivity_B1000.py);
  0/12 reported AUC cells moved beyond combined MC SE. The B=1000 re-run at the n=20000 run of record
  was infeasible in runtime (the AUC bootstrap is ~10 min per scenario even at R=200: B x R resamples,
  each an O(n log n) rank AUC on 40k points), so the check is at n=5000 per the reviewer's fallback.
  The iid-control AUC undercoverage is NOT a small-B artifact: at n=5000 it is 0.936/0.926 (naive/MBB)
  at B=1000 vs 0.934/0.924 at B=200 -- unchanged; the limitation stands.

## 2026-09-24 — P120–P126: submission hardening (additive; sim-frozen and prereg-v1 untouched)

- **P123 corpus denominators separated (reporting defect, not a result change).** The manuscript
  used the word "resolved" for two different populations: the SF-2 coding set (every screened
  record coded for which estimand its reported uncertainty targets, 20 of 31 resolved) and the
  narrower in-frame pool of the retired H1 (which also requires a time-aware split and a reported
  interval, 5 of 16 = 31%). Table 5 reported the first while the sentence introducing it quoted the
  second. Both are now named explicitly wherever either appears, and both are driven by generated
  macros (`\NsfTwo*` from `corpus/sf2_uncertainty_kind.csv`, `\Ninframe*` from the screening log),
  so they cannot drift apart again. No count changed; no claim changed.

- **P124 long-memory boundary located (new result).** The paper previously tested a single Hurst
  value, H=0.8, and reported that ESS-Wilson fails there. `scripts/hurst_sweep.py` now sweeps
  H in {0.55, 0.6, 0.7, 0.8, 0.9} holding the generator, threshold rule, n=5000, R=500, B=200 and
  seed 0 fixed. ADDITIVE: the script calls `t13.sim.coverage_run` with scenario kwargs built in the
  script, so `SCENARIOS` and `sim.py` are untouched and `sim-frozen` still describes the
  instrument. The H=0.8 arm reproduces the reported `lrd_H0.8` cell exactly (ESS-Wilson 0.548,
  MBB 0.600), which is asserted by both `scripts/check_abstract.py` and
  `tests/test_hurst_sweep.py`. RESULT: ESS-Wilson covers 0.96, 0.93, 0.82, 0.55, 0.33 across the
  grid; mean n_eff of the score series falls 1087 -> 64; the plug-in leads the moving block at
  H=0.7 and trails it at H=0.8. The prose claims monotonicity and that reversal, and the guard
  fails the build if either stops holding. This is one Gaussian family on one axis and is stated
  as such (Appendix A.11).

- **P125 retired H3a arm removed from the release.** `corpus/claims.csv` (header-only, never
  populated), `src/t13/audit.py` and `scripts/survival.py` are deleted. Two independent reasons, both
  already on record: the in-frame pool resolved 5 of 16 records so no claim could be coded, and
  `docs/calibration_findings.md` found that inflating a reported SE by sqrt(stream DIF) is not
  justified by the loss-difference's own dependence, which is why prereg v0.6 already dropped the
  summary-only survival arm. `docs/h3a_schema.md` is kept and marked RETIRED. Reachable at
  `sim-frozen`. No claim in the paper depended on any of it.

- **P126 artifact hygiene.** `env/environment.yml` reconciled from Python 3.11 to the 3.13.7 pins
  that actually produced `results/` (it had been flagged stale in `requirements.txt` since the
  freeze). Data-availability statement resolved: AAL window features on reasonable request, raw
  MQTT stream not redistributed. The DOI contradiction between `paper/declarations.md` (claimed
  minted) and the manuscript (stated not attached) resolved in favour of the manuscript; minting
  from `submission-v2` is recorded as the one outstanding author action. README corrected (stale
  figure path, stale test count, both denominators). `results/CONTAMINATED_pre_diagnosis/` is
  KEPT deliberately and now documented in ARTIFACT.md: it records the 2026-09-19 estimand defect
  and its diagnosis, and nothing in the paper reads from it.

- **P122 reporting rule promoted.** Table 1 (the six-row reporting rule) moved from Limitations
  into the Objective section, where it follows C1-C4. It is the paper's deliverable and was
  previously reachable only after the limitations. Appendix A regrouped from 18 flat items into 12
  under four headings (corpus / telemetry estimates / resampling / generator); no objection was
  dropped, and the long-memory item was rewritten against the sweep.

## 2026-09-27 — P127–P133: pre-submission audit

- **P127 the reporting gate does not detect long memory on the series it is applied to (new
  result, and a correction to the paper's own recommendation).** The prespecified gate --- Geyer
  and batch means within 2x, n_eff >= 50 --- was stated on "the series". Applied to the benign
  ALARM INDICATOR, which is where ESS-Wilson takes its n_eff from, it admits 0.99 of replicates at
  H=0.8 and 0.92 at H=0.9, where the interval covers 0.55 and 0.33. Thresholding at a 1% rate
  discards most of the score's serial structure, so the indicator's tau is 3.6 at H=0.9 where the
  benign score's is 74: a long-memory score yields a short-memory-looking indicator and both
  estimators agree about the wrong series. Applied to the benign SCORE series the same rule tracks
  coverage: 1.00 at H<=0.6, 0.89 at 0.7, 0.40 at 0.8, 0.11 at 0.9. The reporting rule is restated
  on the score series; the previous draft stated one row in terms of H, which an analyst cannot
  observe. diagnostics/p127_gate_vs_memory.py -> diagnostics/p127_gate.csv; Table 13 and
  Figure 3. check_abstract.py fails the build if either gate ordering stops holding.

- **P128 Elsevier generative-AI declaration was missing from the manuscript.** It existed only in
  paper/declarations.md, which is not the submitted document. Elsevier requires the statement in
  the manuscript before the references. Added, adapted from declarations.md. Given this paper's
  subject and the extent of AI involvement, its omission would have been a serious compliance gap.

- **P129 ethics statement was a medical-template leftover.** It read "No patient-identifying
  information is used" for a paper whose own telemetry comes from a live ambient-assisted-living
  deployment. Replaced with a statement of what the AAL series actually contain, verified against
  the feature list: numeric 60-minute window aggregates (counts, rates, inter-arrival summaries,
  scalar entropy and diversity statistics), no payload, topic string, identifier or location. The
  institutional position is NOT stated because only the authors know it; logged as an outstanding
  author action in declarations.md.

- **P130 two verified citations had been dropped.** llmeval2026autocorr and llmeval2026resolution
  are recorded in docs/reference_verification.csv as "cited S2 as adjacent-domain precedent,
  author verified", but no \cite for either survived the S2 rewrite at 02058cd. Restored to
  Related work, scope-limited, and added to the cited-not-read appendix item at abstract level.

- **P131 unreferenced float and unreachable appendices.** Table tab:covrec (recall coverage, a main
  results table) had no in-text callout. Appendices app:methods and app:seed were never pointed to
  from the body. All three now referenced.

- **P132 hand-typed result numbers.** The paper claims no result number is typed by hand; three
  were: the window median 3.5 and packet value 2 in S4.4, the qualifying-feature count "three" in
  C2 and Appendix A, and an n_eff-only pass rate 0.63 introduced by P127 itself. All replaced with
  generated macros.

- **P133 submission hygiene.** SF-1/SF-2 were used throughout and never expanded; now defined at
  first use. Keywords in the manuscript and paper/keywords.txt disagreed (6 vs 8) and are now
  synced and guarded. Documentclass declared letterpaper while geometry set a4paper. One vague
  intensifier ("substantially increases") replaced with the two coverage figures. Colour names
  carried a medical journal's name; renamed. paper/template_paper.tex, another paper's template,
  was tracked in the release and is removed. CITATION.cff updated to v0.4.0 with all three authors.

## 2026-09-27 — P134–P137: reproducibility verification before release

- **P134 full re-run of `make sim` against the committed baseline.** Everything reproduced
  byte-for-byte except two columns, both now resolved.
  - `results/coverage_sim.csv`, the `bjk` (block-jackknife) column only. CAUSE: the file was
    written 2026-09-19 06:03; `block_jackknife_auc` was changed at 08:47 the same day to cap the
    block count (an O(n^2/L) runtime fix at small L), and the factorial was never re-run. The
    committed `bjk` column was therefore produced by code that is not in the release. Now
    regenerated. IMPACT: 5 rows, maximum change 0.016. The cap binds only when L is small, so the
    `lrd_H0.8` row is unchanged at 0.538 — and that is the only `bjk` row any prose number depends
    on, so the appendix's B=200 vs B=1000 jackknife comparison (0.54 to 0.49) remains a valid
    post-fix comparison. The only visible change is the block-jackknife column of the AUC coverage
    table. No claim changed; `make all` still passes every guard.
  - `results/hurst_sweep_meta.csv`, the `wall_s` column only. CAUSE: `scripts/hurst_sweep.py`
    recorded wall-clock time in a committed CSV, which is machine-dependent and dirtied the tree on
    every rerun while every scientific value was identical. Timing is now printed to the console and
    kept out of the file.

- **P135 the artifact did not build for anyone but the authors.** `Makefile` defaulted to
  `PY ?= ../../ml_env/bin/python`, a path that exists only in the authors' directory layout. A
  fresh `git clone` failed on the first rule, so the manuscript's claim that `make all` regenerates
  the tables and rebuilds the paper was false for every reader. The default is now `python3`, with
  an override documented in the Makefile and the README.

- **P136 README rewritten for a reader rather than the authors.** The previous README was an
  internal status log. The released one states the problem, the three intervals and where each
  works, the long-memory boundary, the gate result, a worked example that was executed before being
  published, and the layout. It still carries the qualifying medians that `check_abstract.py`
  verifies, so the released README cannot drift from the results either.

- **P137 attribution and citation metadata.** Three early commits were made under a default local
  git identity; `.mailmap` maps them to the author without rewriting history, which would change
  every commit hash. `ARTIFACT.md` now cites the frozen points by tag name instead of by bare
  commit hash. `CITATION.cff` updated to v0.4.0 with all three authors.

- **Probe, not adopted: a two-level recall variance.** The manuscript diagnoses the recall shortfall
  as a between-campaign variance component the attack-subsequence tau cannot see. That diagnosis is
  confirmed: an ad-hoc two-level estimator raises coverage in the dependent cell at n=20000 from
  0.863 to 0.927, at nearly double the width. The principled form, a cluster-robust variance with a
  t critical value on ~5 campaign clusters, does worse than the reported plug-in (0.848) and damages
  the campaigns-only cell (0.950 to 0.915). No defensible replacement exists at this cluster count,
  so nothing was changed and the shortfall stands as reported. Recorded as future work.
