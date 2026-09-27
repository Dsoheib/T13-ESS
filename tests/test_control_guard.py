"""P2 fix: a control guard that actually discriminates.

The old test_iid_coverage_smoke asserted coverage >= 0.75 against the pre-diagnosis
(contaminated) estimand, so it passed at 0.81 while the control was broken. This guard
scores the iid FPR interval against the THRESHOLD-CONDITIONAL truth (the correct estimand)
and (a) passes at nominal, (b) fails when the interval is artificially narrowed to inject
the ~0.81-type miscoverage. A guard that cannot fail on an injected defect is not a guard.
"""
import sys; sys.path.insert(0, "src")
import numpy as np
from t13.sim import generate, conditional_truth, SCENARIOS
from t13 import ci as C


def iid_fpr_coverage(R=300, n=3000, fpr=0.01, seed=0, shrink=1.0):
    """Coverage of the Wilson FPR interval vs the threshold-conditional truth under iid.
    shrink < 1 narrows the interval about its centre to inject miscoverage."""
    kw = SCENARIOS["iid"]; rng = np.random.default_rng(seed); hits = []
    for _ in range(R):
        a, s = generate(2 * n, rng=rng, **kw)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < 20 or a_te.sum() < 20 or (a_te == 0).sum() < 20:
            continue
        thr = np.quantile(s_tr[a_tr == 0], 1 - fpr)
        cond = conditional_truth(thr, kw["mu"], kw.get("rho", 0.0), kw.get("H"))
        alarms = (s_te[a_te == 0] > thr).astype(float)
        c, lo, hi = C.wilson(alarms.sum(), alarms.size)
        if shrink != 1.0:
            lo, hi = c - (c - lo) * shrink, c + (hi - c) * shrink
        hits.append(lo <= cond["fpr"] <= hi)
    return float(np.mean(hits))


def test_control_passes_at_nominal():
    cov = iid_fpr_coverage()
    assert cov >= 0.92, f"iid control undercovers the conditional estimand: {cov}"


def test_guard_catches_injected_miscoverage():
    cov = iid_fpr_coverage(shrink=0.5)   # halve the half-width -> ~0.8-type defect
    assert cov < 0.90, f"guard failed to catch injected miscoverage: {cov}"
