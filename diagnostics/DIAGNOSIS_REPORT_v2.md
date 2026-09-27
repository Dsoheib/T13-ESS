# T1.3 diagnosis report v2 — 2026-09-19 (post-review re-run)

Answers the second verdict (P9–P16). One coverage implementation now (`t13.sim.coverage_run`);
`corrected_coverage.py`, `one_replication`, `floor_curve` deleted. Every cell dual-reported.
Paper still unbuilt. Data: `results/coverage_sim.csv` (+`_meta`), `results/control_iid_R1000.csv`,
`results/split_2x2.csv`, `diagnostics/p13_episode.csv`.

## P9 — the R_used drop mechanism, and dual reporting

**Mechanism.** In the campaign scenarios a randomly-placed test window frequently contains
very few attack samples; when a class is too small to *form* an interval (recall's normal/ESS
need >=2–3 attack points; the ACF needs >=3) the interval is **non-computable** for that rep.
This is selection on exactly the hardest cases (few attacks = worst recall precision), so the
old "coverage over computable reps" biased coverage upward. FPR is essentially always
computable (benign is the majority class), so its cells are unaffected (comp_rate 1.0).

**Fix.** `coverage_run` now reports, per (metric, interval):
`cov_uncond` (non-computable counts as a miss — HEADLINE), `cov_cond` (computable reps only),
and `comp_rate`. Example (bg_iid+campaign, recall/ESS): cov_uncond **0.702** vs cov_cond 0.954
at comp_rate 0.736 — the conditional figure is optimistic by 25 points.

## Acceptance criterion 2 — iid control, R=1000 (`control_iid_R1000.csv`)

| metric | interval | cov_uncond | MC SE | comp_rate |
|---|---|---|---|---|
| FPR | naiveWilson | 0.956 | 0.006 | 1.0 |
| FPR | corrWilson | 0.959 | 0.006 | 1.0 |
| recall | naiveNormal | 0.953 | 0.007 | 1.0 |
| recall | ESS | 0.964 | 0.006 | 1.0 |
| AUC | naiveBoot | 0.933 | 0.008 | 1.0 |
| AUC | mbb | 0.924 | 0.008 | 1.0 |

Control >= 0.93 with MC SE <= 0.01 for FPR and recall. **AUC bootstrap is mildly low
(0.924–0.933)** — a known finite-sample undercoverage of percentile/basic bootstrap AUC,
present even under independence; declared as a limitation, not a dependence effect.

## P11 / H4 — factorial decomposition (R=500, headline cov_uncond)

background {iid, AR(0.9)} x labels {scattered, campaign}. dif_score and comp_rate from meta.

| cell (bg / labels) | FPR naive | FPR corr | recall naive | recall ESS(cond) | AUC naive | AUC mbb(cond) | recall comp_rate |
|---|---|---|---|---|---|---|---|
| iid / scatter (control) | 0.950 | 0.954 | 0.946 | 0.954 | 0.934 | 0.924 | 1.00 |
| iid / campaign | 0.960 | 0.960 | 0.700 | 0.954 | 0.688 | 0.830 | 0.74 |
| AR / scatter | **0.600** | **0.934** | 0.872 | 0.926 | 0.912 | 0.926 | 1.00 |
| AR / campaign | **0.592** | 0.922 | **0.324** | 0.760 | **0.260** | 0.775 | 0.72 |

**Isolation (this is H4):**
- **FPR is degraded by the BACKGROUND factor only** (Δ ≈ 0.36 across background; Δ ≈ 0.01 across
  labels). Benign is a contiguous autocorrelated run, so background dependence inflates its
  variance; campaigns do not touch it.
- **recall/AUC are degraded by CAMPAIGN labels, chiefly through the episode/computability floor,
  not through interval width.** In iid/campaign the *conditional* recall is still 0.954 — the
  interval width is fine — but 26 % of windows are non-computable, so the headline is 0.700.
  With scattered attacks on an AR background (AR/scatter) recall stays 0.872 because scattered
  attack samples land far apart on the AR process and are nearly independent.
- **Both sources together** (AR/campaign): within-campaign autocorrelation + few episodes
  collapse recall/AUC to 0.32/0.26.

**Where the correction actually works:** AR/scatter — pure background dependence with plenty of
episodes — corrections restore all three (FPR 0.934, recall-ESS 0.926, AUC-mbb 0.926). The
shortfall elsewhere is the episode floor (campaign cells) or long memory, not a failure of the
estimator.

## Acceptance criterion 3 / H6 — 2x2 split (`split_2x2.csv`, AR/campaign, R=500)

| split | FPR naive | FPR corrWilson | (MC SE) |
|---|---|---|---|
| random | 0.724 | 0.732 | 0.020 |
| temporal | 0.592 | **0.922** | 0.012 |

**H6 holds for FPR:** temporal-corrected (0.922) > random-corrected (0.732), non-overlapping MC
SE. Under the random split the correction does nothing (0.724 → 0.732): shuffling drives
tau_hat → 1, so no widening is applied — the time order the correction needs was destroyed.
H6 is **retained**.

## P13 — episode bootstrap: FLOOR, not bug (`p13_episode.csv`)

AR(0.9) background, fixed threshold, attack episodes swept 5→200:

| E_attack | naive | ESS | mbb | episode |
|---|---|---|---|---|
| 5 | 0.510 | 0.873 | 0.835 | 0.853 |
| 20 | 0.545 | 0.945 | 0.917 | 0.938 |
| 100 | 0.527 | 0.953 | 0.938 | 0.950 |
| 200 | 0.487 | 0.958 | 0.932 | 0.953 |

Episode-bootstrap coverage **rises monotonically to nominal as episodes grow** (naive stays
flat at ~0.5). The 0.22–0.32 seen in the campaign scenarios corresponds to windows with only
1–3 attack episodes — below this range, consistent with the H5 episode floor. **Not a bug;
retained and reported with the episode count.**

## P16 — conflation gap recorded

Recorded as SF-1 in `docs/simulation_findings.md`: naive-normal FPR covers 0.830 against the
population (deployment) estimand vs 0.932 against the threshold-conditional estimand, **under
independence** — a 10-point, dependence-free defect from threshold-estimation variance. The
charitable-estimand choice is now stated in the claim (README) and prereg v0.6.

## P14 / P7 — housekeeping
- One coverage implementation (`coverage_run`); duplicates deleted; 17 tests pass.
- Env frozen from the actual interpreter (Python 3.13.7; `env/ACTUAL_ENV.txt`, `requirements.txt`).
- `results/CONTAMINATED_pre_diagnosis/` retained untouched.

## Revised belief
Dependence breaks naive intervals against the charitable estimand. The correction **restores
near-nominal coverage when dependence is short-memory background with enough independent
episodes** (AR/scatter: 0.93 for all three metrics; FPR under short memory generally). It does
**not** reach nominal when attacks are few long campaigns (episode floor) or under long-range
dependence. The paper's claim is the conditional-repair-plus-floor statement, plus the
dependence-free conflation gap (SF-1) — not a universal "we fix the interval".

## Still blocked (correctly)
Real-data DIF and corpus. H2 note (P12): tau_hat is biased low where tau is largest (few
episodes), so the DIF table will **understate** dependence — report it as a directional
(conservative) bias, and for the attack class expect "no interval reportable" (n_eff below the
floor) rather than a corrected interval, on CICIDS-style benchmarks.
