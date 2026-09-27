# Simulation findings (prereg-exempt)

Findings that emerged from the coverage simulation itself, not from a pre-registered
hypothesis. Recorded here so they are not laundered into the audit as if pre-planned.

## SF-1 — The conflation gap: test-set CIs undercover the deployment estimand even under independence

Source: `diagnostics/p1_estimand.py`, iid scenario, R=1000, threshold learned on the training
half.

| interval | estimand | coverage | MC SE |
|---|---|---|---|
| naive-normal FPR | population (deployment) | 0.830 | 0.012 |
| naive-normal FPR | threshold-conditional | 0.932 | 0.008 |

**There is no dependence in this scenario.** The ~10-point gap is pure threshold-estimation
variance: a test-set interval is computed *at the threshold learned on finite training data*,
so it targets the metric at that realised threshold (conditional), but the field reads and
uses its CIs as statements about deployment performance (the population value under the true
operating point). The interval does not carry the threshold's own sampling variance, so as a
deployment statement it undercovers by ~10 points **before any dependence is considered**.

This is a second defect of the same class as the dependence one (an interval that omits a
variance component), and it is *orthogonal* to it: dependence inflates the within-test-set
variance; threshold estimation adds a between-split variance. A complete deployment interval
must carry both. The paper should state this as a distinct, dependence-free contribution.

## Simulation-only hypotheses (moved out of the prereg 2026-09-19; NOT confirmatory)

These were pre-registered as descriptive but are properties of the synthetic generator, not
claims about the literature; they belong here, not in the confirmatory prereg. All confirmed at
n=5000, R=500 (see `diagnostics/DIAGNOSIS_REPORT_v2.md`); n=20000 confirmation pending.

- **SF-H4 (decomposition).** Background autocorrelation degrades metrics computed over
  contiguous samples (FPR on the benign run); campaign labels degrade recall/AUC chiefly via the
  episode/computability floor. Isolated by the background x label factorial: FPR Δ≈0.36 across
  background, ≈0.01 across labels; recall/AUC break in the campaign cells. CONFIRMED.
- **SF-H5 / SF-H7 (episode / effective-epoch floor).** When a test window holds few independent
  attack episodes (n_eff of the attack stream small), no resampling attains nominal coverage for
  recall; episode-bootstrap coverage rises 0.85→0.95 as episodes 5→200 (`p13_episode.csv`). The
  reportable quantity below the floor is the episode count / n_eff, not an interval. CONFIRMED.
- **SF-H6 (random splits).** REFRAMED after P18 (`p18_within_test.csv`): a random split BOTH
  genuinely lowers within-test dependence (benign τ 19.7→10.3, because neighbours are split
  across the partition) AND hides the residual from the estimator (seen τ→1.04 while true τ=10.3),
  so the correction is a no-op and the naive interval still undercovers (FPR 0.72). Temporal-
  corrected (0.92) > random-corrected (0.73), non-overlapping MC SE. Retained as a simulation
  finding, not a headline claim.
- **SF-H8 (AUC residual).** The percentile/basic bootstrap for AUC undercovers mildly even under
  independence (0.924–0.933 at R=1000) — a finite-sample bootstrap-of-U-statistic effect. NOTE:
  Dehling & Wendler (2010) give the CLT/bootstrap for U-statistics under *mixing* asymptotically;
  it does **not** establish finite-sample iid coverage, so it does not "explain away" this. Stated
  as a small, unresolved control caveat on AUC, not a citation-closed point (per P20).

## The charitable-estimand choice (must appear in the claim)

All dependence-miscoverage numbers in this project are measured against the **threshold-
conditional** estimand — the one *most favourable to the authors being audited*, because it
excludes the SF-1 threshold-estimation gap. We audit under the estimand that gives published
intervals the best possible coverage, and they still fail under dependence. Stating the
charitable choice converts a fix (adopting the right estimand) into a strength (the audit
cannot be dismissed as measuring the wrong, harder quantity).

## SF-2 (P67) — modal uncertainty statement is not test-set sampling uncertainty (corpus finding)
Screening (uncertainty_kind over 10 resolved papers): none 5, seed-dispersion 2, fold-dispersion 1,
test-set-CI 2. Of the 5 reporting ANY uncertainty, only 2 report a TEST-SET interval; 3 report
dispersion across random SEEDS or CV FOLDS. Seed/fold dispersion measures model-fitting instability
on a FIXED test set: it -> 0 as seeds/folds grow while the metric's true sampling uncertainty stays
put, and DIF does not correct it (different estimand). A third defect of the same class as SF-1;
reported as its own category (uncertainty_kind), not folded into H3a.

### SF-2 simulation (P70, additive vs sim-frozen) -- measured divergence
`diagnostics/sf2_seed_vs_testset.py` (bg_ar__lab_campaign, fixed test set, FPR@1%): the seed-based
standard error shrinks while the true test-set sampling sd is constant.
| K seeds | seed_std | seed_SE | testset_sd(true) | seed_SE/testset_sd |
|---|---|---|---|---|
| 2 | 0.0031 | 0.0022 | 0.0034 | 0.64 |
| 20 | 0.0033 | 0.0007 | 0.0034 | 0.21 |
| 200 | 0.0033 | 0.0002 | 0.0034 | 0.068 |
seed_SE -> 0 as K grows; testset_sd constant. Per-K ratio seed_SE/testset_sd (understatement factor):
K=2: 0.64 (~1.6x too small), K=5: 0.48 (~2x), K=10: 0.28 (~3.6x), K=20: 0.21 (~5x), K=50: 0.14,
K=100: 0.093, K=200: 0.068 (~15x). **Real papers report 5-10 seeds, so the operative understatement
is ~2-3.6x (K=5-10), NOT the K=200 figure** (quoting K=200 would be cherry-picking the extreme cell).

**Sharper claim (which practice fails): mean +/- STD vs mean +/- SE.** seed_std is ~constant
(0.0031-0.0033) and here lands near testset_sd (0.0034). So a paper reporting mean +/- STD across
seeds lands near the right MAGNITUDE (by coincidence in this scenario -- std measures model-fitting,
testset_sd measures sampling; their ratio is not general), whereas a paper reporting mean +/- SE (or a
seed-CI) understates and gets WORSE as K rises. The failing practice is specifically SE-/CI-over-seeds,
not std-over-seeds. SF-2 is a measured result, not an argument.
