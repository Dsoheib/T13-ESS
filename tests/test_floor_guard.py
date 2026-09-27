"""P22 regression: (1) an AR(1) rho=0.9 series written to CSV and read back THROUGH THE
ADAPTER recovers DIF ~19 (adapter path covered, not just the estimator); (2) the estimator-floor
guard raises when Geyer floors at 1.0 while batch-means sees strong dependence."""
import sys, os, tempfile; sys.path.insert(0, "src")
import numpy as np, pandas as pd
import pytest
from scipy.signal import lfilter
from t13.dif import integrated_autocorrelation_time as tau, dif, EstimatorFloorError
from t13.datasets import to_grain


def _ar1(n, rho, seed=0):
    rng = np.random.default_rng(seed); z = rng.normal(0, 1, n)
    z[0] = rng.normal(0, 1 / np.sqrt(1 - rho ** 2))
    return lfilter([1.0], [1.0, -rho], z)


def test_ar1_recovers_dif_through_adapter():
    n = 60000; x = _ar1(n, 0.9)
    df = pd.DataFrame({"t": np.arange(n), "y": (np.arange(n) % 20 == 0).astype(int), "f": x})
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "ar1.csv"); df.to_csv(p, index=False)
        back = to_grain(pd.read_csv(p), "flow")           # adapter path: sorts by t
    got = dif(back["f"].values)                            # analytic tau = 19
    assert 12.0 < got < 30.0, got                          # dependence recovered, not floored


def test_floor_guard_no_false_positive_on_white_noise():
    """A genuinely near-white series (MA(1), theta=-0.9): Geyer floors to 1.0 AND batch is ~1,
    so the guard must NOT raise -- 1.0 is the correct answer here."""
    rng = np.random.default_rng(3); e = rng.normal(0, 1, 60001)
    x = e[1:] - 0.9 * e[:-1]                                # rho_1 < 0 -> Geyer floors
    tg, _ = tau(x, "geyer", guard=False); tb, _ = tau(x, "batch")
    assert tg <= 1.0 + 1e-9 and tb < 5, (tg, tb)
    assert dif(x) <= 1.0 + 1e-9                             # no raise, returns 1.0 legitimately


_WEATHER = os.path.join(os.path.dirname(__file__), "..", "..", "toniot_data", "IoT_Weather.csv")


@pytest.mark.skipif(not os.path.exists(_WEATHER), reason="TON_IoT-Weather not present")
def test_floor_guard_fires_on_real_epoch_confound():
    """Real TON_IoT-Weather benign temperature (corrupt/epoch-confounded order): Geyer floors to
    1.0 while batch-means = 16.3 -> the guard MUST raise rather than report a bogus DIF=1.0."""
    d = pd.read_csv(_WEATHER, low_memory=False); d.columns = [c.strip() for c in d.columns]
    dt = pd.to_datetime(d["date"].astype(str).str.strip() + " " + d["time"].astype(str).str.strip(),
                        format="%d-%b-%y %H:%M:%S", errors="coerce")
    d = d.assign(t=dt, y=pd.to_numeric(d["label"], errors="coerce")).dropna(subset=["t", "y"]).sort_values("t").reset_index(drop=True)
    y = d["y"].astype(int).values; cap = 120000; best, bb = 0, -1.0
    for i in range(0, len(y) - cap, cap // 4):     # most class-balanced contiguous window (as calibration)
        p = y[i:i + cap].mean(); bal = min(p, 1 - p)
        if bal > bb: bb, best = bal, i
    w = d.iloc[best:best + cap]
    ben = pd.to_numeric(w.loc[w.y == 0, "temperature"], errors="coerce").dropna().values
    with pytest.raises(EstimatorFloorError):
        tau(ben, "geyer", guard=True)


def test_shuffle_collapses_dif():
    """Documenting the failure mode: shuffling an AR(1) drives DIF to 1 (rho_1 -> 0)."""
    x = _ar1(40000, 0.9, seed=2)
    xs = np.random.default_rng(0).permutation(x)
    assert dif(xs) < 1.15                                  # shuffled -> no recoverable dependence
