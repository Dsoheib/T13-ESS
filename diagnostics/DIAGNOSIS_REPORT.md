# T1.3 diagnosis report — 2026-09-19

Response to the REJECT/REPEAT verdict. Every coverage number below carries R and Monte-Carlo
SE = sqrt(p(1-p)/R). Paper left unbuilt (reverted). No new figures/tables for the manuscript.

## Headline

The reviewer was right: the control had failed and "results confirm the claim" was wrong.
The cause was an **estimand mismatch**, not dependence. After fixing the estimand and the
rare-event interval, the iid control sits at nominal, and the picture of the correction is
**more modest than claimed**: dependence badly breaks naive intervals, but the correction
fully repairs only FPR under short memory and otherwise closes the gap only partially, with a
residual floor. I no longer believe "the correction repairs the interval" as a general claim.

---

## P1 — control failure diagnosed (`p1_estimand.py`, iid, R=1000)

Coverage of the interval against three candidate estimands:

| metric | interval | estimand | coverage | MC SE |
|---|---|---|---|---|
| FPR | naive-normal | population | 0.830 | 0.012 |
| FPR | naive-normal | window-conditional | 0.831 | 0.012 |
| FPR | naive-normal | **threshold-conditional** | 0.932 | 0.008 |
| FPR | ESS-plugin | threshold-conditional | 0.937 | 0.008 |
| FPR | **Wilson** | **threshold-conditional** | **0.953** | 0.007 |
| FPR | MBB | threshold-conditional | 0.915 | 0.009 |
| recall | naive-normal | threshold-conditional | 0.941 | 0.007 |
| recall | **ESS-plugin** | **threshold-conditional** | **0.951** | 0.007 |
| AUC | naive-boot | population (=cond) | 0.944 | 0.007 |

**Conclusion.** A test-set interval conditions on the training-learned threshold; its estimand
is the metric **at that threshold** (threshold-conditional), not the population value under a
re-learned threshold. Scoring against the population truth (the original code) produced the
0.81–0.83 "control failure". Against the correct estimand the control is nominal. Two defects:
(1) wrong estimand for threshold-dependent metrics; (2) rare-event FPR needs Wilson, not the
normal/ESS approximation (0.932 → 0.953). AUC is threshold-free, so it never had the gap
(0.944) — which independently confirms the mechanism.

## P4 — estimator is sound; the scenario is mixed (`p4_tau_vs_n.py`, R=40)

tau_hat (Geyer) vs analytic tau, by n:

| series | analytic tau | n=5k | 10k | 20k | 40k |
|---|---|---|---|---|---|
| AR(1) rho=0.9 | 19.0 | 20.4 | 19.5 | 19.2 | 19.3 |
| Markov labels (p_stay=.995) | 379 | 176 | 241 | 370 | 353 |
| fGn H=0.8 | inf | 36 | 43 | 67 | 78 |

**Conclusion.** For AR(1) the estimator is flat in n and matches analytic 19 — **not broken**.
fGn grows with n, correct for long memory. The apparent "n_eff saturates at ~176" came from
the accuracy/label-driven series whose analytic tau is ~379: at n<=40k there are only ~13–100
independent campaigns, so tau_hat is biased low and extremely noisy (SD ~= mean at n=5k).
Implication: the scenario named `dependent` **mixes** a short-memory AR(1) background (tau=19)
with campaign labels (tau~379). Metrics that depend on labels (recall, accuracy) inherit the
long correlation length; the prereg's `dependent` vs `lrd` distinction is blurred and must be
restated, and DIF on real data must be reported with the reliability gate (n_eff<50 flag).

## P5 — cannot be closed: there is no git history

The folder **was never a git repository** (verified: `git rev-parse` failed before this run).
The v0.1/v0.2/v0.3 "statuses" are prose in the README, not commits. There is no artifact to
`git diff`, so the 0.92 → 0.75 movement of the 2x2 cannot be attributed to a commit. I also
overwrote the prior `split_2x2.csv` during the first (rejected) run, so the earlier value is
not recoverable from disk. This is a genuine reproducibility failure, now mitigated: I ran
`git init` and committed the state, so future movements are attributable. The 2x2 is not
re-run here — under the diagnosis its previous numbers were computed against the wrong estimand
and are void regardless.

## P2 — regression guard fixed (`tests/test_control_guard.py`)

New guard scores iid FPR against the threshold-conditional estimand:
- nominal: **0.947** (passes, gate >= 0.92);
- injected miscoverage (interval half-width x0.5): **0.707** (caught, gate < 0.90).

The old `test_iid_coverage_smoke` (gate >= 0.75, contaminated estimand path) is now `skip`ped
with a reason; it validated the wrong quantity and could not have caught 0.81.

---

## Revised coverage at R>=500, correct estimand + Wilson FPR (`results/coverage_sim.csv`)

Coverage vs the threshold-conditional truth (AUC vs population). "naive" = correction OFF.

| scenario | dif_score | metric | naive | corrected(best) | corrected route |
|---|---|---|---|---|---|
| iid | 1.0 | FPR | 0.950 | 0.956 | Wilson-ESS |
| iid | 1.0 | recall | 0.946 | 0.956 | ESS |
| iid | 1.0 | AUC | 0.926 | 0.920 | MBB |
| campaigns_only | 56 | FPR | 0.953 | 0.956 | (benign iid -> naive fine) |
| campaigns_only | 56 | recall | 0.939 | 0.959 | ESS (within-campaign iid) |
| campaigns_only | 56 | AUC | 0.909 | 0.843 | MBB **worse** |
| dependent | 30 | FPR | **0.604** | **0.923** | Wilson-ESS |
| dependent | 30 | recall | **0.456** | 0.775 | ESS (not nominal) |
| dependent | 30 | AUC | **0.321** | 0.777 | MBB (not nominal) |
| lrd_H0.8 | 84 | FPR | 0.421 | 0.620 | MBB (far from nominal) |
| lrd_H0.8 | 84 | recall | 0.396 | 0.657 | ESS (far) |
| lrd_H0.8 | 84 | AUC | 0.399 | 0.712 | BJK (far) |
| heavy_tail | 28 | FPR | 0.408 | 0.886 | MBB |
| heavy_tail | 28 | recall | 0.356 | 0.598 | ESS (far) |
| heavy_tail | 28 | AUC | 0.353 | 0.746 | MBB (not nominal) |

All cells: R_used 343–500, MC SE <= 0.027. Full long-format table with per-cell MC SE in
`results/coverage_sim.csv`; per-scenario dif/n_eff/reliability in `results/coverage_sim_meta.csv`.

### What this supports and what it does not
- **Supported:** (1) the control is nominal (dependence, not a bug, is what the other cells
  measure now); (2) under dependence, naive intervals are **severely anticonservative even
  against the correct estimand and even after a time-aware split** (FPR 0.60/0.42/0.41,
  recall 0.46/0.40/0.36, AUC 0.32/0.40/0.35 for dependent/lrd/heavy_tail); (3) the FPR
  correction (Wilson on n_eff) **restores nominal under short memory** (dependent 0.923).
- **Not supported:** "the correction repairs the interval" in general. Recall and AUC
  corrections improve markedly but **do not reach nominal** at n=5k (recall 0.60–0.78, AUC
  0.71–0.78); under long memory even FPR is not repaired (0.62). The **episode bootstrap is
  consistently bad** (0.22–0.32) and should be dropped or restricted to genuinely
  episode-independent data.
- **Residual floor (the defensible secondary claim, P3):** recall/AUC coverage is capped by
  the number of independent attack episodes and by long memory; no resampling closes it here.

## Answer to the explicit question
Do I still believe the correction repairs the interval? **No.** The evidence says: dependence
breaks the interval; the correction fully repairs **FPR under short memory only**, and
otherwise **reduces but does not close** the deficit, with a floor set by episode count and
long memory. The paper's honest headline is "naive intervals are anticonservative under
dependence, with a coverage floor," not "we fix the interval." The abstract/README claim
must be rewritten to match before any manuscript work resumes.

## Not yet done (correctly still blocked)
- `sim.py` / `run_coverage_sim.py` still compute the OLD estimand; they are quarantined, not
  yet merged with the fix. The corrected experiment lives in `diagnostics/corrected_coverage.py`.
  Merging the estimand fix into the canonical pipeline is the next code step.
- Real-data DIF and the corpus remain blocked (same estimator under review; now cleared, but
  the pipeline merge should land first).
- P8: `hidden2026variable` is the preprints.org item (unrefereed, single-author, June 2026).
  Not silenced. Decision for the author: exclude, or keep in the volume stratum with status
  stated. Left as-is in refs.bib pending that decision.
