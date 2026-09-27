# Artifact — T1.3 (dependence-aware interval evaluation for IDS)

Everything in the paper is regenerated from this repository by one command. No result number is
hand-typed. Tables come from `scripts/make_tables.py`, and so do the figures quoted in the prose:
the same script writes `paper/tables/prose_macros.tex`, whose macros carry the coverage,
episode-curve, threshold-mismatch, block-length and telemetry values the text cites.
`scripts/check_abstract.py` fails the build if a macro disagrees with the CSV it came from, if a
generated macro stops being used in the text, or if the abstract's restated dependence-inflation
figures drift.

## Reproduce
```
conda env create -f env/environment.yml    # reconciled 2026-09-24 to the interpreter that made results/
make all                                    # test -> tables -> abstract-check -> figures -> paper/main.pdf
```
`env/environment.yml`, `requirements.txt` and `env/ACTUAL_ENV.txt` now agree (Python 3.13.7 and the
pins under which every committed CSV was generated). Earlier revisions of `environment.yml` declared
Python 3.11 and did not describe the run.
`make all` runs: the unit tests (`tests/`), table generation (`scripts/make_tables.py` ->
`paper/tables/*.tex` + `corpus_macros.tex` + `prose_macros.tex`), the number-provenance guard
(`scripts/check_abstract.py`), and the LaTeX compile. `make paper` depends on that guard, so the
PDF cannot be built around it. `make sim` reruns the coverage simulation, the block-length sensitivity
(`scripts/block_length_sensitivity.py`) and the Hurst sweep (`scripts/hurst_sweep.py`).

The guard is not only a drift check. It also fails the build when the Hurst sweep's `H=0.8` arm
stops reproducing the reported long-memory cell exactly, when ESS-Wilson coverage or mean `n_eff`
stops being monotone in `H`, or when the plug-in/moving-block ordering stops reversing between
`H=0.7` and `H=0.8` -- i.e. whenever a sentence in the long-memory subsection would become false.

## Freeze order (dated in `prereg/CHANGELOG.md`, which ships here)
This artifact is a single snapshot of the submitted state, not a version history. The order in
which things were frozen is what matters for the claims, and it is on the record in the
pre-registration change log:

- The **pre-registration** was frozen before the corpus was coded.
- The **instrument** (`src/t13/{sim,dif,ci}.py`) was frozen after the n=20000 confirmation and was
  not changed for any real-data work. Later additions -- the Hurst sweep and the gate diagnostic --
  are additive scripts that call the frozen functions with parameters built in the script; they do
  not modify `sim.py` or its `SCENARIOS`, and the Hurst sweep's H=0.8 arm reproduces the originally
  reported cell exactly, which `scripts/check_abstract.py` enforces on every build.
- Every deviation from the pre-registration is logged, dated, and reasoned in
  `prereg/CHANGELOG.md`, including the ones that cost the paper a hypothesis.

## Retired: the H3a claim-coding arm (not in this release)
`corpus/claims.csv`, `src/t13/audit.py` and `scripts/survival.py` implemented the pre-registered
H3a arm: code per-claim estimates and standard errors out of published papers, inflate the reported
SE by sqrt(DIF), and re-test. None of it is here, for two independent reasons. (i) It was never
populated: the in-frame pool resolved 5 of 16 records to full text, so `claims.csv` never had a row
and shipping a header-only CSV would misrepresent the artifact. (ii) `docs/calibration_findings.md`
found that inflating by sqrt(stream DIF) is not justified by the loss-difference's own dependence --
differential and stream DIF diverge by two orders of magnitude -- so the pre-registration dropped
the summary-only survival arm before submission. The schema is kept as a record in
`docs/h3a_schema.md`, marked RETIRED. No claim in the paper depends on any of it.

## What is included
- `src/t13/` instrument; `tests/` (39 tests, 1 skipped without TON_IoT); `scripts/` (sim, tables,
  DIF, Hurst sweep, calibration, checks).
- `results/` regenerable CSVs; `diagnostics/` (p1 estimand, p4 tau-vs-n, p13 episode, p18 within-test,
  SF-2 simulation, diagnosis reports).
- `corpus/` — `inclusion_log.csv` (every screened record with decision, reason, criterion,
  distribution_used), `criteria.md` (verbatim screening criteria, Option A), `screening_results.csv`,
  `sf2_uncertainty_kind.csv`, `adversarial_review_batch.md`.
- `prereg/` (frozen + CHANGELOG), `docs/` (all findings), `paper/` (LaTeX + generated tables).
- `results/CONTAMINATED_pre_diagnosis/` -- the pre-2026-09-19 coverage run, kept deliberately. Its
  README states the two defects that invalidated it (an estimand mismatch that drove the i.i.d.
  control to 0.81, and a rare-event interval choice) and points at the diagnostics that found them.
  It is part of the record of the correction, not a stray output. Nothing in the paper reads from it.
- `env/` environment spec.

## What is NOT included (and why)
- Raw datasets (`data/raw/`, pcaps, CICIDS/TON_IoT/AAL CSVs): not redistributed; `data/order/` +
  `scripts/*_dif.py` document how each was obtained and time-order-audited. CICIDS2017
  GeneratedLabelledFlows is on the Hugging Face mirror `bencorn/CICIDS2017`.
- The AAL MQTT-bridge telemetry is the authors' own; availability stated in the paper.

## Real-data producers (P100) and `make realdata`
Every committed real-data CSV now has a named producer; `make realdata` regenerates them from raw.
Raw is not redistributed -- fetch it first with `scripts/fetch_raw.py --url <mirror> --out data/raw`,
which writes `data/MANIFEST.sha256` (byte hashes recorded from the fetched files; `--verify` re-checks).

| CSV | producer | raw input | status |
|---|---|---|---|
| `dif_by_dataset.csv` (AAL rows) | `scripts/aal_dif.py` | `../bridgeguard_features/features_labeled.csv` (present) | **regenerated + diffed: bit-for-bit identical** (max \|Δ\|=0.0) |
| `dif_by_dataset.csv` (CICIDS flow rows) | `scripts/cicids_dif.py` | CICIDS2017 Wednesday flows | producer exists; raw re-fetch needed to diff |
| `differential_dif.csv` | `scripts/cicids_dif.py` | CICIDS2017 Wednesday flows | producer exists; raw re-fetch needed to diff |
| `time_order_audit.csv` | `scripts/time_order_audit.py` | CICIDS2017 flows | producer exists; raw re-fetch needed to diff |
| `cicids_flow_dif.csv` | `scripts/flow_dif_producer.py` (**written for P100**) | CICIDS2017 Mon/Tue/Wed flows | previously hand-assembled; producer now written; raw re-fetch needed to diff |
| `packet_windows.csv` | `scripts/pcap_window_dif.py --csv` (**producer mode added for P100**) | CICIDS2017 daily pcapng | previously hand-assembled; producer now written; raw re-fetch needed to diff |

The local CICIDS2017 copy (downloaded during the acquisition study, ~283,876,488 bytes) is no longer
on disk, so the CICIDS/packet producers were written but not re-run here; the AAL producer was run
and diffed. `cicids_flow_dif.csv` emits `dif_a_asshipped` (never "upperbound", P91).

## Reliability / honesty properties
- Screening is single-coder (Option A); the full log + verbatim criteria ship here so any reader can
  re-screen. Inter-rater reliability is not claimed (Limitations).
- The estimator carries a temporal-order guard and a Geyer/batch agreement flag; DIF is reported per
  metric, per grain, with the flag.
