"""P4 diagnosis: does tau_hat_int grow with n (long-memory / broken estimator) or converge
to the generator's analytic tau (correct short-memory estimator)?

Series with KNOWN analytic tau:
  AR(1) rho:            tau = (1+rho)/(1-rho)                     [finite -> must NOT grow with n]
  2-state Markov labels: tau = (1+lam)/(1-lam), lam = 1 - p10 - p01   [finite]
  fGn Hurst H>0.5:      tau diverges (long memory) -> tau_hat SHOULD grow with n (by design)

We estimate tau by every rule at n in {5k,10k,20k,40k}, over reps, and print tau_hat +- SD
beside the analytic value. Acceptance: for the finite-tau series, tau_hat within its SD of
analytic and flat in n. If tau_hat grows in n for AR(1), the Geyer sum is not terminating.
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from scipy.signal import lfilter
from t13.dif import integrated_autocorrelation_time, RULES
from t13.sim import fgn, markov_labels


def ar1(n, rho, rng):
    z = rng.normal(0, 1, n); z[0] = rng.normal(0, 1 / np.sqrt(1 - rho ** 2)) if rho else z[0]
    return lfilter([1.0], [1.0, -rho], z)


def analytic_ar1(rho):
    return (1 + rho) / (1 - rho)


def analytic_markov(p_stay=0.995, prevalence=0.05):
    p10 = 1 - p_stay
    p01 = (1 - p_stay) * prevalence / (1 - prevalence)
    lam = 1 - p10 - p01
    return (1 + lam) / (1 - lam)


def study(ns=(5000, 10000, 20000, 40000), R=40, seed=0):
    rng = np.random.default_rng(seed)
    series = {
        "ar1_rho0.9": (lambda n: ar1(n, 0.9, rng), analytic_ar1(0.9)),
        "markov_labels": (lambda n: markov_labels(n, 0.995, 0.05, rng).astype(float), analytic_markov()),
        "fgn_H0.8": (lambda n: fgn(n, 0.8, rng), np.inf),
    }
    rows = []
    for name, (gen, tau_true) in series.items():
        for n in ns:
            est = {r: [] for r in RULES}
            for _ in range(R):
                x = gen(n)
                for r in RULES:
                    est[r].append(integrated_autocorrelation_time(x, r)[0])
            row = {"series": name, "n": n, "tau_analytic": tau_true}
            for r in RULES:
                e = np.array(est[r]); row[f"{r}_mean"] = round(e.mean(), 1); row[f"{r}_sd"] = round(e.std(), 1)
            rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--R", type=int, default=40); a = ap.parse_args()
    df = study(R=a.R)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    df.to_csv("diagnostics/p4_tau_vs_n.csv", index=False)
