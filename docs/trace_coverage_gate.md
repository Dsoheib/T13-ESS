# Week 2 gate

Gate 2 miss: ESS-Wilson unconditional false-positive coverage is below 0.90 at n=5000 or n=20000. The miss is the result.

Pre-specified floor: unconditional ESS-Wilson coverage >= 0.90 at both sample sizes.
The verdict uses the primary series, Monday Flow Duration.
Threshold frozen from a length-400,000 block-bootstrap draw, seed 12345. R=500.
Blocks are non-wrapping. Labels are the campaign chain, independent of the trace.

## Reference

- Flow Duration: Geyer 43.47, batch 22.32, agree True, L 87, max |z| 2.7. Reference FPR 0.0100 (repeat gap 0.0002), recall 0.2136 (repeat gap 0.0138). Mean alarm-indicator DIF 2.21 at n=5000, 2.59 at n=20000.
- Flow Packets/s: Geyer 5.68, batch 5.52, agree True, L 12, max |z| 11.1. Reference FPR 0.0002 (repeat gap 0.0000), recall 0.0113 (repeat gap 0.0006). Mean alarm-indicator DIF 1.00 at n=5000, 1.00 at n=20000.

## Reading

The primary miss is the n=5000 cell (0.862). At n=20000 the same ESS-Wilson interval covers at 0.924. The nominal-n interval covers at 0.730 at n=5000.
A companion whose reference false-positive rate is far from 0.01 has its threshold on a tie. That cell does not test whether the correction repairs undercoverage.

## Unconditional coverage

- Flow Duration n=5000 fpr ESS-Wilson: 0.862 ± 0.015 (conditional 0.862, computable 1.000).
- Flow Duration n=5000 fpr naiveWilson: 0.730 ± 0.020 (conditional 0.730, computable 1.000).
- Flow Duration n=5000 recall ESS: 0.514 ± 0.022 (conditional 0.659, computable 0.780).
- Flow Duration n=5000 recall naiveNormal: 0.320 ± 0.021 (conditional 0.409, computable 0.782).
- Flow Duration n=20000 fpr ESS-Wilson: 0.924 ± 0.012 (conditional 0.924, computable 1.000).
- Flow Duration n=20000 fpr naiveWilson: 0.728 ± 0.020 (conditional 0.728, computable 1.000).
- Flow Duration n=20000 recall ESS: 0.796 ± 0.018 (conditional 0.801, computable 0.994).
- Flow Duration n=20000 recall naiveNormal: 0.414 ± 0.022 (conditional 0.416, computable 0.994).
- Flow Packets/s n=5000 fpr ESS-Wilson: 0.956 ± 0.009 (conditional 0.956, computable 1.000).
- Flow Packets/s n=5000 fpr naiveWilson: 0.956 ± 0.009 (conditional 0.956, computable 1.000).
- Flow Packets/s n=5000 recall ESS: 0.532 ± 0.022 (conditional 0.713, computable 0.746).
- Flow Packets/s n=5000 recall naiveNormal: 0.512 ± 0.022 (conditional 0.683, computable 0.750).
- Flow Packets/s n=20000 fpr ESS-Wilson: 0.946 ± 0.010 (conditional 0.946, computable 1.000).
- Flow Packets/s n=20000 fpr naiveWilson: 0.946 ± 0.010 (conditional 0.946, computable 1.000).
- Flow Packets/s n=20000 recall ESS: 0.852 ± 0.016 (conditional 0.854, computable 0.998).
- Flow Packets/s n=20000 recall naiveNormal: 0.816 ± 0.017 (conditional 0.818, computable 0.998).
