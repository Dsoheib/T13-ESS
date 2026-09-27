# Calibration findings — TON_IoT-Fridge, TON_IoT-Weather (2026-09-19)

> **RETRACTED 2026-09-19 (review P21/P22).** This calibration is INVALID and its DIF numbers
> must not be used. Two defects: (1) construct validity — TON_IoT Fridge/Weather are per-device
> SENSOR telemetry, not flow records, so they do not test H2's flow-feature population; (2) time
> order is UNRECOVERABLE — `results/time_order_audit.csv` shows 68% of consecutive pairs have
> Δt<=0, unique-timestamp fraction ~0.29, and 17%/4% duplicate rows, so DIF=1.0 was the Geyer
> floor on a non-temporal series (now caught by the EstimatorFloorError guard), not a finding.
> H2 is UNMEASURED (not void). A valid calibration needs a time-order-audited FLOW dataset
> (CICIDS2017 / CICIoT2023 / MAWIFlow). The text below is kept only as the record of what was
> rejected and why.


Two NAMED datasets, **declared excluded from the confirmatory corpus** (used only to exercise
the DIF pipeline on real telemetry and get a first read on H2 and H3b). Real, time-ordered IoT
sensor streams (date+time+label). Most class-balanced contiguous 120k-row window used so a
detector pair can be fit. Data: `results/dif_by_dataset.csv`, `results/differential_dif.csv`.

## Stream DIF (flow grain), benign class, with segment CI

| dataset | series | dif_geyer | dif_batch | dif_ci | reliable | Geyer/batch agree |
|---|---|---|---|---|---|---|
| Fridge | fridge_temperature\|benign | 1.0 | 1.0 | [1.0,1.1] | yes | yes |
| Fridge | iforest/logreg/rf score(benign) | 1.0 | 1.0 | [1.0,1.1] | yes | yes |
| Weather | temperature\|benign | 1.0 | 16.3 | [1.0,62.8] | yes | **no** |
| Weather | pressure\|benign | 3.5 | 25.2 | [1.0,1.0] | yes | **no** |
| Weather | humidity\|benign | 5.4 | 23.7 | [1.0,61.6] | yes | **no** |
| Weather | iforest score(benign) | 152.1 | 23.5 | [1.0,187.8] | **no** | **no** |
| Weather | logreg score(benign) | 1.0 | 10.3 | [1.0,153.9] | yes | **no** |
| Weather | rf score(benign) | 17.9 | 15.0 | [1.0,19.0] | yes | yes |

## H2 read (acceptance: median DIF >= 1.5 at some grain, else H2 void / paper converts)

At **flow grain** the benign-score DIF is **~1.0 on Fridge** and **1–152 but Geyer/batch-
disagreeing and unreliable on Weather**. Median across the estimable benign-score series is
**~1**, below the 1.5 materiality floor. So at flow grain **H2 does not hold on TON_IoT**. This
is the P12 / week-3 risk materialising: flows/records are already aggregated and often close to
independent. Consequence (as pre-registered): the DIF story must move to the **window/packet
grain** and to the **n_eff-reporting spine (H3a)**; a corrected *interval* is defensible only
where the benign stream is genuinely dependent and short-memory. Window-grain DIF on these and
other datasets is the next measurement before H2 is declared void corpus-wide.

## Epoch-confound finding (reportable)

The label DIF is 7028 (Fridge) / 8885 (Weather) and **flagged unreliable** — an artifact of the
class-vs-time confound: TON_IoT ships benign records then attack records, so the label sequence
is one long run, not a stationary dependence. The genuine chronological interleaving of the two
regimes is not recoverable from the shipped order. **TON_IoT time order is therefore reported as
epoch-confounded**, exactly the failure mode the prereg reserves for "time order unrecoverable".
(Also directly relevant to the group's IoMT-Sentinel epoch-confound work.)

## Differential DIF (H3b gate)

DIF of the paired 0/1 loss-difference d_t = loss_A - loss_B at the 1% operating point (the
quantity a Diebold-Mariano / "A beats B" test's variance depends on):

| dataset | pair | dif_diff (Geyer) | dif_diff CI | stream DIF (A benign) | mean_loss_diff |
|---|---|---|---|---|---|
| Fridge | iforest-logreg | 30.3 | [1.0,1.1] | 1.0 | +0.0013 |
| Fridge | iforest-rf | 1.0 | [1.0,1.1] | 1.0 | +0.0003 |
| Fridge | logreg-rf | 6.6 | [1.0,1.1] | 1.0 | -0.0010 |
| Weather | iforest-logreg | 403 | [1.0,164] | 152 | -0.0085 |
| Weather | iforest-rf | 942 | [1.0,239] | 152 | -0.0245 |
| Weather | logreg-rf | 428 | [1.0,139] | 1.0 | -0.0160 |

**Verdict on H3b (summary-only arm):** *inconclusive on this calibration data, leaning DROP.*
The differential DIF is **not reliably estimable** here — point Geyer estimates (30–942) and
their segment CIs (lower bound ~1, upper bound in the hundreds) disagree by two orders of
magnitude, driven by the same epoch block structure. Critically, differential DIF and stream
DIF **diverge** (Fridge logreg-rf: differential 6.6 vs stream 1.0; Weather logreg-rf:
differential 428 vs stream 1.0), so inflating a reported SE by sqrt(stream DIF) is **not**
justified by the loss-difference's actual dependence. Recommendation carried into prereg v0.6:
**drop the summary-only sqrt(stream-DIF) arm**; compute survival only from released data via the
paired block-bootstrap (`ci.paired_difference_ci`), whose block length is set from the
loss-difference series directly. A clean confirmation needs a dataset with short-memory benign
and no epoch confound; TON_IoT provides neither.

## Net effect on the paper (feeds P17)
Flow-grain DIF is weak/unstable on real TON_IoT telemetry, and the loss-difference DIF is not
reliably estimable. Both push the spine toward **"report n_eff, not an interval"** (H3a), with a
corrected interval claimed only for FPR under demonstrably short-memory benign backgrounds.
