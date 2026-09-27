# Phase 11 — claim audit (2026-09-20)

Every claim the paper will make, classified against its evidence. SUPPORTED / PARTIALLY SUPPORTED /
UNSUPPORTED / OVERSTATED. Anything not SUPPORTED gets evidence or leaves the paper.

| # | Claim | Evidence | Class | One-sentence form for the paper |
|---|---|---|---|---|
| 1 | Dependence breaks naive intervals under the charitable (threshold-conditional) estimand, even after a time-aware split | corrected_coverage n=5000 & n=20000: AR cells naive FPR 0.56–0.60, recall 0.32–0.48, AUC 0.26–0.37 vs cond truth; iid control ~0.95 | **SUPPORTED** | "Under serial dependence, i.i.d. test-set intervals cover the threshold-conditional metric at 0.3–0.6 versus the nominal 0.95, even after a time-aware split." |
| 2 | Correction repairs FPR under short memory; only partially recovers recall/AUC; fails under long memory | dependent: corrWilson FPR 0.92–0.95; recall-ESS 0.66–0.88; AUC-mbb 0.75–0.86; lrd FPR 0.55 | **SUPPORTED (scoped)** | "Dependence-aware intervals restore near-nominal FPR coverage under short-memory background, partially recover recall and AUC (bounded by the episode floor), and do not repair under long-range dependence." |
| 3 | The reportable quantity is n_eff (effective-epoch floor) | p13_episode: episode-bootstrap 0.85→0.95 as episodes 5→200; floor at n_eff<50 | **SUPPORTED** | "Below roughly 50 effective episodes no resampling attains nominal coverage, so the honest report is the effective sample size, not an interval." |
| 4 | Random splitting is partly easier AND uncorrectable (SF-H6) | p18: benign τ true 19.7→10.3, seen 1.04; 2×2 temporal-corr FPR 0.92 vs random-corr 0.73 (non-overlapping) | **SUPPORTED** | "A random split both lowers the true within-test dependence and hides the residual from the estimator (seen τ≈1 vs true ≈10), so its interval undercovers and cannot be corrected." |
| 5 | DIF is feature- and capture-dependent; no single number per dataset | multi-day: Flow Bytes/s 1.1 (Mon) vs 63.9 (Wed); packet inter-arrival 2/163/152 across windows | **SUPPORTED** | "The dependence-inflation factor varies by feature, day, and capture window, so a single per-dataset DIF is not well defined; it must be reported per metric and grain." |
| 6 | Three-grain DIF magnitudes on genuine, confound-controlled data, with the AAL anchor | packet inter-arrival 23–75 (true pcap order); flow (b) median 17.3, confound-robust (P35 shuffle+dedup); AAL window median 96 | **SUPPORTED** | "Benign-stream dependence is large across grains on real, time-order-audited data — packet inter-arrival DIF 23–75, flow (conservative) median 17.3, AAL-bridge window 96 — and is genuine serial dependence, not an ordering or clustering artifact." |
| 7 | SF-1 conflation gap (test-set CIs undercover the deployment estimand even under independence) | p1_estimand iid R=1000: naive-normal FPR vs population 0.830, vs threshold-conditional 0.932 | **SUPPORTED** | "Even with no dependence, a test-set interval undercovers the deployment metric by ~10 points because it omits the variance of the training-learned threshold." |
| 8 | SF-2 seed/fold estimand: field uncertainty is usually absent or seed/fold dispersion, a different estimand | corpus resolved n=20: 75% none, 5 reporters, only 2 test-set intervals (strict-18: 72% none); sim seed_SE/testset_sd = 0.48/0.28 at K=5/10 | **SUPPORTED (n stated)** | "Where the field reports uncertainty at all it is usually dispersion across random seeds or CV folds — a model-fitting quantity whose standard error shrinks with more seeds (≈2–3.6× too small at 5–10 seeds) and never estimates the metric's sampling uncertainty (resolved n=20; 11 unresolved)." |
| 9 | Release-practice / NOT-ASSESSABLE: order-destroyed releases make intervals uncorrectable | time_order_audit: TON_IoT 68% Δt≤0, 3:1 ts collisions; CICIoMT2024 no timestamp; MachineLearningCVE drops timestamp; MAWIFlow public = random samples | **SUPPORTED** | "Many benchmarks are consumed in releases that destroy time order (dropped or colliding timestamps, class-balanced samples), so published intervals on them cannot be corrected by any reader." |
| 10 | The one-line reporting requirement | follows from 1–9; instrument produces it | **SUPPORTED (recommendation)** | "Report the effective sample size and DIF per metric and grain (with the Geyer/batch agreement flag) and state the uncertainty_kind." |
| 11 | Novelty vs HED, Bay 2023, Lew 2026, Arp 2022 | Gate-1 full-text reads: Arp's 10 pitfalls contain no ESS/interval pitfall; Bay 2023 explicitly exchangeable-not-serial; Lew grades presence not estimand; HED is a metric not interval inference | **SUPPORTED** | "No prior work transports dependence-adjusted interval inference to serial IDS telemetry: Arp's pitfalls omit it, biostatistics corrects clustered (not serial) AUC, Lew grades whether statistics are present not which estimand they target, and HED changes what is scored not its uncertainty." |

## Claims REMOVED from the paper (would be OVERSTATED/UNSUPPORTED if kept)
- **H1 prevalence** ("X% of time-aware papers fail to correct") — RETIRED: insufficient resolvable
  denominator (31% resolution). Not stated.
- **"The field adopted temporal splits, but none repairs the interval"** (the round-1 premise) —
  WITHDRAWN (P66): adoption is near zero; the claim is replaced by the split-agnostic form (claims
  1+4). Would be OVERSTATED if kept.
- **"Time-aware splits are rare" as a contribution** — DEMOTED to a descriptive observation
  attributed to Arp/TESSERACT/Lew (not novel; P65).
- **"The correction repairs the interval" (general)** — never claimed; scoped to claim 2.
- **Corpus as an audit / prevalence** — DEMOTED to illustrative sample (P68).

## Residual caveats carried honestly (not claims)
- SF-H8: percentile/basic AUC bootstrap undercovers mildly even iid (0.92–0.93) — stated limitation.
- SF-2 std-vs-SE: mean±std over seeds lands near the right magnitude by scenario coincidence; the
  failing practice is SE-/CI-over-seeds. Stated precisely, not overclaimed.

## Verdict
All 11 retained claims are SUPPORTED (two scoped, one a recommendation, one with n stated). No
retained claim is UNSUPPORTED or OVERSTATED. The four would-be-overstated claims are removed/demoted
and logged. Phase 11 clears.

## Addendum (2026-09-23) — after the Q1 weeks 1–3

The table above is the pre-registration audit. It is not rewritten. The manuscript headline is the qualifying subset, not the pre-QC magnitudes in claim 6.

- Claim 6's packet 23–75, flow median 17.3, and window 96 are pre-QC. The manuscript reports the qualifying medians (Geyer and batch means within 2×, and \(n_{\mathrm{eff}}\ge 50\)).
- Week 1, metric-level intervals on the alarm indicator, the attack indicator, and label-score pairs: qualifying false-positive widths exceed the pre-specified factor \(\sqrt{1.5}\). Monday Isolation Forest false-positive DIF is 2.37 (width ratio 1.55, \(n_{\mathrm{eff}}\) 14113). The only paired flip is Wednesday logistic regression minus random forest AUC, estimate −0.0073. At \(B=1000\) the moving-block interval is still [−0.0188, 0.0009]. The loss-difference interval for that pair excludes zero under both schemes. Larger gaps stay significant under both intervals.
- Week 2, Monday Flow Duration, frozen threshold, moving-block resample of the benign prefix: ESS–Wilson unconditional false-positive coverage is 0.862±0.015 at \(n=5000\) and 0.924±0.012 at \(n=20000\). The pre-specified gate was 0.90 at both sizes. The miss at \(n=5000\) is the result. The nominal-\(n\) interval at \(n=5000\) is 0.730±0.020. Flow Packets/s sits on a tie and does not test the correction.
- The Student-\(t\) row was scored against the Gaussian conditional formula. It is omitted from the coverage tables and is not a coverage claim.
- Recall clock, own seed, short-memory campaign generator: subsequence and missing-on-the-original-clock unconditional coverage differ by 0 at \(n=5000\) and by 0.008 at \(n=20000\), both within two combined Monte Carlo standard errors. The reported interval keeps the subsequence. These figures do not replace the coverage-simulation recall numbers.
- The six-row reporting rule in the manuscript is a recommendation. It includes the Monday shortfall. It does not promise nominal coverage on that trace at \(n=5000\).
