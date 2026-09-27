# Week 1 gate

Gate 1 met: at least one paired comparison excludes 0 under the i.i.d. interval and includes 0 under the moving-block interval.

Pre-specified width factor: sqrt(1.5) = 1.225.
Bootstrap replicates: B = 200. Paired intervals are basic on both arms.
CICIDS cap: 67,000 contiguous flows in as-shipped row order.
AAL benign: attack_type == normal. time_sin and time_cos are excluded from the detector features.

## Order and class counts

- CICIDS2017-Mon: rows 67000, attack 0, benign 67000, detectors iforest, train attack 0, test attack 0.
- CICIDS2017-Tue: rows 67000, attack 7917, benign 59083, detectors iforest, logreg, rf, train attack 3092, test attack 4825.
- CICIDS2017-Wed: rows 67000, attack 4973, benign 62027, detectors iforest, logreg, rf, train attack 807, test attack 4166.
- AAL-MQTT-bridge: rows 7772, attack 2422, benign 5350, detectors iforest, logreg, rf, train attack 784, test attack 1638.

## Material widths (qualifying FPR or recall)

- CICIDS2017-Mon iforest fpr: estimate 0.0055, width ratio 1.546, DIF 2.37, n_eff 14113.4.
- CICIDS2017-Tue iforest fpr: estimate 0.0075, width ratio 1.311, DIF 1.71, n_eff 16746.0.
- CICIDS2017-Tue logreg fpr: estimate 0.0071, width ratio 1.749, DIF 3.03, n_eff 9463.3.
- CICIDS2017-Tue rf fpr: estimate 0.0126, width ratio 1.772, DIF 3.12, n_eff 9179.4.
- CICIDS2017-Tue rf recall: estimate 0.9977, width ratio 3.026, DIF 9.16, n_eff 526.8.
- CICIDS2017-Wed iforest fpr: estimate 0.0132, width ratio 7.082, DIF 45.64, n_eff 642.7.
- CICIDS2017-Wed logreg fpr: estimate 0.0109, width ratio 2.736, DIF 7.36, n_eff 3987.6.
- CICIDS2017-Wed logreg recall: estimate 0.5931, width ratio 3.573, DIF 12.77, n_eff 326.3.
- CICIDS2017-Wed rf fpr: estimate 0.0254, width ratio 4.250, DIF 17.75, n_eff 1652.8.
- CICIDS2017-Wed rf recall: estimate 0.8795, width ratio 4.502, DIF 20.27, n_eff 205.5.
- AAL-MQTT-bridge iforest fpr: estimate 0.0138, width ratio 2.022, DIF 3.80, n_eff 591.0.
- AAL-MQTT-bridge iforest recall: estimate 0.6758, width ratio 1.596, DIF 2.55, n_eff 642.7.
- AAL-MQTT-bridge logreg fpr: estimate 0.0111, width ratio 1.666, DIF 2.63, n_eff 854.3.
- AAL-MQTT-bridge rf fpr: estimate 0.0294, width ratio 2.242, DIF 4.82, n_eff 466.2.

## Paired flips (i.i.d. excludes 0, moving block includes 0)

- CICIDS2017-Wed logreg-rf auc_diff: estimate -0.0073, i.i.d. [-0.0103, -0.0032], moving block [-0.0174, 0.0007].

## Reverse flips (moving block excludes 0, i.i.d. includes 0)

- None.

## Sensitivity of the one flip

The only flip is Wednesday logreg−rf AUC, estimate −0.0073. At the pre-specified B=200 the moving-block interval is [−0.0174, 0.0007]. The same seeded comparison at B=1000 is i.i.d. [−0.0112, −0.0035] and moving block [−0.0188, 0.0009], so the flip is not a small-B accident, and the block interval still crosses zero by less than 0.001. The loss-difference interval for that same pair excludes zero under both schemes.
