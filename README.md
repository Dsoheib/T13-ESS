# Dependence-aware intervals for intrusion-detection evaluation

Code and data for *When Confidence Intervals Assume Independence: Dependence-Aware Intervals for
Intrusion-Detection Evaluation* (submitted to *Computers & Security*).

A confidence interval on a test-set metric assumes the rows are exchangeable. Intrusion-detection
telemetry is serially dependent, so that interval can be too narrow. This repository is the
instrument that measures the dependence, the three metric-specific intervals that correct for it,
the coverage simulation that says where each one works, and every table and figure in the paper.

**One command rebuilds the paper from the data.**

```bash
conda env create -f env/environment.yml && conda activate t13-ess
make all
```

If your interpreter is not on `PATH`, pass it in: `make all PY=/path/to/venv/bin/python`.

`make all` runs the test suite, regenerates every table from `results/`, runs a check that fails if
any number in the text has drifted from the file it came from, redraws the figures, and compiles
`paper/main.pdf`. It is idempotent: run it twice and the working tree is unchanged.

## What the paper concludes

| metric | interval | where it works |
|---|---|---|
| false-positive rate | ESS-adjusted Wilson plug-in | reaches ~nominal under short-memory dependence |
| recall | ESS plug-in on the attack subsequence | improves coverage, stays short of nominal |
| AUC | moving-block bootstrap of Mann–Whitney | improves coverage, stays short of nominal |

Two results are worth pulling out.

**The long-memory boundary is located, not just exhibited.** Sweeping the Hurst exponent with
everything else fixed, ESS–Wilson covers 0.96, 0.93, 0.82, 0.55, 0.33 at H = 0.55, 0.6, 0.7, 0.8,
0.9. It holds to about H = 0.6 and degrades monotonically above it.

**A quality gate is only as good as the series you compute it on.** The gate this paper
recommends — two autocorrelation estimators agreeing within 2x, and n_eff at least 50 — admits 92%
of replicates at H = 0.9 when it is computed on the *alarm indicator*, which is where the interval
takes its n_eff from, and the interval it admits covers 0.33. Thresholding at a 1% rate discards the
score's serial structure, so a long-memory score looks short-memory once it is thresholded. Computed
on the *benign score series* instead, the same gate admits 11% there and tracks coverage across the
whole grid. Read the gate on the scores.

**Dependence is present in the telemetry, and it is not one number.** Under the agreement rule the
qualifying flow-grain median is 3.4 and the qualifying window-grain median is 3.5; the packet
qualifying series is about 2. Flow Bytes/s is near 1 on Monday and 64 on Wednesday in the same
capture, which is why the paper reports DIF per metric and per grain rather than per dataset.

## Using the instrument on your own evaluation

```python
import sys; sys.path.insert(0, "src")
import numpy as np
from scipy.signal import lfilter
from t13.dif import agreement, ess
from t13.ci import wilson_ess_ci, wilson

# stand-in for a real evaluation: benign scores in time order, and the alarms they produce
rng = np.random.default_rng(0)
benign_scores = lfilter([1.0], [1.0, -0.9], rng.normal(size=20000))
threshold = np.quantile(benign_scores, 0.99)
alarms = (benign_scores > threshold).astype(float)

# Read the gate on the SCORES, not on the alarms.
gate = agreement(benign_scores, tol=2.0)
n_eff = ess(benign_scores)

if gate["agree"] and n_eff >= 50:
    rate, lo, hi, neff_alarm = wilson_ess_ci(alarms)
    _, nlo, nhi = wilson(alarms.sum(), alarms.size)
    print(f"FPR {rate:.4f}  ESS-Wilson [{lo:.4f}, {hi:.4f}]  (nominal-n [{nlo:.4f}, {nhi:.4f}])")
    print(f"widening factor {(hi-lo)/(nhi-nlo):.2f}x, n_eff(alarm) {neff_alarm:.0f}")
else:
    print(f"gate fails (ratio {gate['ratio_geyer_batch']:.1f}, n_eff {n_eff:.0f}): "
          f"report n_eff and no interval")
```

Running that prints:

```
FPR 0.0100  ESS-Wilson [0.0073, 0.0136]  (nominal-n [0.0087, 0.0115])
widening factor 2.29x, n_eff(alarm) 3883
```
The gate is read on `benign_scores`, not on `alarms` — that is the second result above. On this
AR(1) example the dependence-aware interval is 2.3x wider than the nominal-*n* one, which is the
size of the error a naive interval makes here.

## Layout

| path | what is in it |
|---|---|
| `src/t13/` | the instrument: `dif.py` (autocorrelation, ESS, block length), `ci.py` (the intervals), `sim.py` (the coverage generator) |
| `scripts/` | every producer: coverage simulation, Hurst sweep, real-data DIF, table and figure generation, the number-provenance check |
| `diagnostics/` | the mechanism runs behind the discussion: estimand, width, AUC, the gate |
| `results/`, `diagnostics/*.csv` | every committed result the paper reads |
| `tests/` | 39 tests, including guards that fail if a claim in the paper stops being true |
| `corpus/` | screening criteria, full inclusion log, uncertainty-kind coding |
| `prereg/` | the pre-registration and its deviation log |
| `docs/` | the gate records and findings behind each result |
| `paper/` | LaTeX source, generated tables, figures |

## Reproducing the numbers

`make all` uses the committed results and takes about a minute. To regenerate the results
themselves:

```bash
make sim      # coverage simulation, block-length sensitivity, Hurst sweep, diagnostics (~40 min)
make realdata # the real-data CSVs; needs the raw captures, which are not redistributed
```

Everything seeded in `make sim` reproduces exactly. The raw CICIDS2017 capture is not included:
fetch it with `scripts/fetch_raw.py` (it records SHA-256 hashes of what it downloads). The authors'
MQTT window features are available from the corresponding author on request.

## The build checks the paper against the data

No result in the text is typed by hand. `scripts/make_tables.py` writes every number into LaTeX
macros from the CSVs, and `scripts/check_abstract.py` fails the build if a macro disagrees with its
source, if a generated macro stops being cited, if the abstract drifts, or if one of the claims the
prose makes stops holding — that coverage is monotone in H, that the Hurst sweep still reproduces
the reported cell, that the gate orderings still hold, that the recall clocks still agree within two
combined standard errors.

## Freeze order

This is a snapshot of the submitted state. What matters for the claims is the order things were
frozen in, and that is dated in `prereg/CHANGELOG.md`: the pre-registration was frozen before the
corpus was coded, and the instrument before any real-data analysis. Later additions are additive
scripts that call the frozen functions without modifying them — the Hurst sweep's H=0.8 arm
reproduces the originally reported cell exactly, and the build fails if it ever stops doing so.
Every deviation from the pre-registration is logged, dated and reasoned in that change log,
including the ones that cost the paper a hypothesis.

## Citing

See `CITATION.cff`. Please cite the paper rather than the repository where possible.

## License

MIT (`LICENSE`). CICIDS2017 is cited, not redistributed (Sharafaldin et al., 2018).
