"""Does the reporting gate detect the regime in which its own interval fails?

The reporting rule admits ESS-Wilson when the two autocorrelation estimators agree within 2x and
n_eff >= 50. Applied to the benign ALARM INDICATOR -- the series the interval's n_eff comes from --
that gate passes almost everywhere on the fractional-Gaussian grid, including at H=0.9 where
ESS-Wilson covers 0.33. Thresholding at a 1% rate discards most of the score's serial structure, so
a long-memory score yields a short-memory-looking indicator.

Applied instead to the benign SCORE series the same gate tracks coverage: it admits the cells where
the interval works and rejects the cells where it does not.

Additive: reads the frozen generator through t13.sim.generate, changes nothing in it.
Writes diagnostics/p127_gate.csv.
"""
import sys, argparse
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import SCENARIOS, generate
from t13.dif import integrated_autocorrelation_time as _tau

AGREE_FACTOR = 2.0
NEFF_FLOOR = 50


def gate(x):
    """The prespecified reporting gate: Geyer and batch means within 2x, and n_eff >= 50.
    Returns (passes, agrees, neff_ok, tau_geyer, tau_batch, neff)."""
    tg, _ = _tau(x, "geyer", guard=False)
    tb, _ = _tau(x, "batch", guard=False)
    ratio = max(tg, tb) / max(min(tg, tb), 1e-12)
    neff = len(x) / tg
    agrees = bool(ratio <= AGREE_FACTOR)
    neff_ok = bool(neff >= NEFF_FLOOR)
    return (agrees and neff_ok), agrees, neff_ok, float(tg), float(tb), float(neff)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--H", nargs="*", type=float, default=[0.55, 0.6, 0.7, 0.8, 0.9])
    p.add_argument("--n", type=int, default=5000)
    p.add_argument("--R", type=int, default=500)
    p.add_argument("--fpr", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()

    base = dict(SCENARIOS["lrd_H0.8"])
    rows = []
    for H in a.H:
        kw = dict(base, H=H)
        rng = np.random.default_rng(a.seed)
        acc = {"alarm": [], "score": []}
        tau_acc = {"alarm": [], "score": []}
        for _ in range(a.R):
            y, s = generate(2 * a.n, rng=rng, **kw)
            y_tr, s_tr, y_te, s_te = y[:a.n], s[:a.n], y[a.n:], s[a.n:]
            thr = np.quantile(s_tr[y_tr == 0], 1 - a.fpr)
            benign_scores = s_te[y_te == 0]
            alarms = (benign_scores > thr).astype(float)
            for name, series in (("alarm", alarms), ("score", benign_scores)):
                try:
                    acc[name].append(gate(series)[:3])
                    tau_acc[name].append(gate(series)[3:])
                except Exception:
                    pass
        for name in ("alarm", "score"):
            g = np.array(acc[name], dtype=float)
            t = np.array(tau_acc[name], dtype=float)
            rows.append({"H": H, "series": name, "R": len(g),
                         "gate_pass_rate": round(float(g[:, 0].mean()), 3),
                         "agree_rate": round(float(g[:, 1].mean()), 3),
                         "neff_ok_rate": round(float(g[:, 2].mean()), 3),
                         "median_tau_geyer": round(float(np.median(t[:, 0])), 2),
                         "median_tau_batch": round(float(np.median(t[:, 1])), 2),
                         "median_neff": round(float(np.median(t[:, 2])), 0)})
        print(f"H={H:g} done", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("diagnostics/p127_gate.csv", index=False)
    print(out.to_string(index=False))
