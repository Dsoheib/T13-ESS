# 15 hardest screening decisions — for supervisor adversarial challenge (not reliability)

Challenge any you think wrong; the agent defends or revises. Each: decision, reason, the specific
ambiguity.

1. **arxiv-2508.19450 (CITADEL)** — reports_ci_or_test=**borderline-no**. Reports a single
   aggregate std (18.1%) but no per-run CI / significance test. AMBIGUITY: does a lone std satisfy
   criterion 4 ("standard error / error bar")? Coded NO (aggregate std ≠ reported uncertainty on a
   comparison). Challenge if std-only should count.
2. **arxiv-2602.12183 (SiamXBERT)** — reports_ci_or_test=**no**. "Results averaged over 10 runs to
   reduce variance" but no spread reported. AMBIGUITY: 10-run averaging without reporting the
   spread — is that "reports uncertainty"? Coded NO (averaging is not reporting).
3. **arxiv-2506.18114 (temporal PE)** — time_aware_split=**unclear**. Title says "temporal" but the
   split is an unspecified hold-out (2-of-3 samples). AMBIGUITY: title vs unstated method → coded
   unclear, not yes. Challenge whether "temporal positional encoding" implies a temporal split.
4. **hidden2026 (preprints.org)** — role=**exhibit vs H1 member**. Time-aware split + i.i.d.
   bootstrap CI + no correction → technically an H1 member (the one confirmed), but it is an
   eval-critique preprint, not a primary detector paper. AMBIGUITY: count in the H1 denominator, or
   treat only as the motivating exhibit? Coded: both-flagged (H1 member AND exhibit).
5. **arxiv-2604.21623 (A-THENA)** — include vs exclude. k-fold CV, point estimates, no CI.
   AMBIGUITY: fails criterion 4 (no uncertainty) → EXCLUDE-at-criterion-4, or INCLUDE-but-not-in-H1?
   Coded exclude-crit4. Challenge if k-fold fold-variance (unreported) should count as available.
6. **PMC12656321** — in-scope for audit? random splits + 95% CI + no correction. NOT in H1
   (random), but the clearest H3a target. AMBIGUITY: H1 excludes it (not time-aware); does the
   broader "i.i.d. interval, no correction" observation include it? Coded: H3a-yes, H1-no.
7. **SD-S1570870525000186 vs IEEE IoT-J** — venue coding. This is Elsevier "Internet of Things",
   NOT IEEE "Internet of Things Journal". Coded volume (Elsevier IoT), NOT core (IEEE IoT-J).
   AMBIGUITY: the two same-named venues; easy to miscode as core.
8. **eswa-flowtransformer-2024** — stratum. Expert Systems with Applications is not in the named
   frame. Coded core-adjacent; should it be volume? AMBIGUITY: ESWA is Q1 but unnamed → provisional
   core; challenge → likely volume.
9. **IIoT papers (arxiv-2607.00553, 2501.13962, nature-50690-0)** — criterion 1 domain. IIoT vs
   IoT. Coded INCLUDE (IIoT within scope). AMBIGUITY: does "IoT/IoMT" include Industrial IoT? If
   not, these exclude at criterion 1.
10. **SR2026-47264 / HED-ID (Nature, access-limited)** — split type coded from ABSTRACT ("random
    seeds") not full text (auth-walled). AMBIGUITY: abstract-level coding of the decisive field;
    should be `unclear-no-access`, not `random`. Coded no-access.
11. **red-mnstate-1158 (thesis)** — exclude crit-3 (venue). AMBIGUITY: a thesis is not a frame
    venue, but its content may match; excluded on venue. Challenge if grey-literature belongs.
12. **arxiv-2602.05594 / 2504.07839 (surveys)** — exclude crit-1. Coded exclude (not primary
    studies). AMBIGUITY: surveys sometimes report their own re-evaluation; excluded as non-primary.
13. **mdpi-FI-16-8-284 (Future Internet)** — stratum. Future Internet (MDPI) is not in the named
    volume list (Sensors/Electronics/Sci Rep). Coded volume-adjacent. AMBIGUITY: unnamed MDPI
    venue → include as volume or exclude on criterion 3?
14. **spj-icomputing-0127 (Intelligent Computing, SPJ)** — venue crit-3. Not in frame. Coded
    volume-adjacent. AMBIGUITY: Science Partner Journal not named → include-as-volume or exclude?
15. **arxiv preprints generally** — criterion 3 via P52. All arXiv coded volume-preprint (in-frame
    by the P52 rule). AMBIGUITY: P52 was a post-freeze logged rule; a strict reading of the frozen
    frame excludes arXiv entirely. Challenge whether P52's inclusion of preprints is legitimate or
    should be dropped (which would shrink the pool substantially).

## RULINGS APPLIED (supervisor, 2026-09-20) — logged with reasoning
1/2. Std-only & averaged-runs (CITADEL, SiamXBERT): not criterion-4 test-set intervals; coded
   `seed-dispersion` / `none` per P67, retained in pool under uncertainty_kind. [reviewer P67]
3. temporal-PE (arxiv-2506.18114): now moot — arXiv is OUT of the in-frame denominator (below).
4. hidden2026: EXHIBIT, not H1 member (arXiv/preprint ruling). Labelled non-frame.
5. A-THENA & all arXiv: OUT of H1 denominator — the frozen frame names core+volume venues, not arXiv;
   post-freeze inclusion that enlarges the denominator is what the freeze prevents. Retained as
   non-frame exhibits only. [reviewer: arXiv/P52 reversed]
6. PMC12656321: not in H1 (random split) but IS an H3a test-set-interval target (random-split 95% CI).
7. Elsevier "Internet of Things" (SD-S15708.., SD-S25426..): different venue from IEEE IoT-J -> VOLUME,
   venue recorded verbatim. [reviewer ruling]
8. ESWA / Computer Networks / J.Franklin: not named in frame -> OUT. [reviewer: unnamed venues out]
9. IIoT papers: IN scope (IoT subclass; Edge-IIoTset already on dataset list). [reviewer ruling]
10. Nature SciRep access-limited (HED-ID resolved via PMC; SR2026-47264 & TACNet auth-walled) ->
    resolved where PMC exists, else no-access.
11-12. thesis / surveys: OUT (crit-3 venue / crit-1 non-primary). [confirmed]
13-14. Future Internet (MDPI) / Intelligent Computing (SPJ): OUT — volume names only Sensors,
    Electronics, Scientific Reports. [reviewer: unnamed MDPI/SPJ out]
15. arXiv preprints generally: OUT of denominator, exhibits only. [reviewer ruling]
