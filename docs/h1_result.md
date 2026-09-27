# Screening summary (DEMOTED to illustrative sample) + SF-2 distribution — rev 2026-09-20

**The corpus is an illustrative sample, not an audit.** n = 5 in-frame full-text-resolved (SciRep x4
via PMC + Sensors x1); full-text resolution reached 31% of the in-frame pool, with 69% access-blocked
(IEEE Xplore, ScienceDirect, MDPI-403, Nature-auth). No prevalence claim is made. The corpus
illustrates the reporting requirement; it does not measure the field.

## H1 — RETIRED (not void, not measured)
Retired for insufficient resolvable denominator (31% < 60% target; access-blocked remainder). Recorded
in CHANGELOG with the rate as the reason. See P68/P71.

## Adoption of time-aware splits — descriptive only, attributed to prior work
Among the full-text-resolved records, 0 use a time-aware split (all random / k-fold / hold-out). This
is consistent with and ATTRIBUTED TO Arp et al. 2022, Pendlebury et al. 2019 (TESSERACT), and Lew et
al. 2026, which establish low temporal-split adoption from larger, better-constructed corpora. Not a
contribution; not a headline. Per SF-H6 the paper's claim does not depend on it (whatever the split,
the interval is wrong; the random-split majority is not even assessable).

## SF-2 — corpus finding, reported on RESOLVED records only (P71)
`none` is the only category assignable by absence, so abstract/snippet coding systematically inflates
it. Therefore SF-2 is reported on records whose uncertainty_kind was resolved from full text, arXiv
abstract, or a results table/caption — NOT from abstract silence. corpus/sf2_uncertainty_kind.csv.

**Strict fetched (full text + arXiv abstract), n=18:** none 13 (72%), seed 2, fold 1, test-set-CI 2.
**Resolved incl. 2 results-table checks (RT-Cabi, Frontiers), n=20:** none 15 (75%), seed 2, fold 1,
test-set-CI 2 — 5 reporters, of which **only 2 report a test-set interval**.
**Unresolved (uncertainty_kind not determinable without full text): n=11 — reported as UNKNOWN, not
none.**

- Of the ~5 papers that report ANY uncertainty, **only 2 report a test-set interval**; the rest report
  seed/fold dispersion — a different estimand (SF-2) that DIF cannot correct. 0 resolved records
  correct for within-test dependence.
- Sharp sub-point: one resolved paper (Frontiers) runs 5-fold CV but reports only AVERAGED points, so
  even the fold dispersion is hidden → `none`. Averaging over folds/seeds destroys the very dispersion
  that was computed.
- Unoccupied relative to Lew et al. (who graded whether statistics are PRESENT): SF-2 measures which
  ESTIMAND they target. Direction is stable across the strict-18 and resolved-20 cuts; the 11 unknown
  are stated as unknown.

## H3a denominator (re-keyed, P66) — test-set-interval reporters, any split
= the `test-set-CI` records (2 resolved; both i.i.d., 0 corrected). Access-limited; SF-H6 justifies
including all splits. Seed/fold-dispersion records are NOT in H3a (SF-2 instead).
