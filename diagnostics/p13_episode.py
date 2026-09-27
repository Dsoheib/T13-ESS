"""P13: is the episode bootstrap's 0.22-0.32 coverage a bug or the H5 episode floor?

Controlled design: AR(0.9) background over the whole series (so recall is genuinely serially
dependent -> episode resampling is the RIGHT tool), E attack episodes of fixed length Lc
separated by benign gaps, fixed threshold (no threshold-learning noise). Coverage of the
recall interval vs the threshold-conditional truth, as E grows 5 -> 200.

Verdict rule (reviewer): if episode-bootstrap coverage rises toward nominal as E grows, it is
the floor (correct, inefficient at low E). If it stays flat and low at E=200, it is a bug.
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from scipy.signal import lfilter
from scipy.stats import norm
from t13 import ci as C


def make_series(E, Lc=20, gap=200, rho=0.9, mu=2.0, rng=None):
    """E attack episodes of length Lc, benign gaps of length `gap`, AR(rho) background."""
    a = []
    for _ in range(E):
        a.extend([0] * gap); a.extend([1] * Lc)
    a.extend([0] * gap)
    a = np.array(a, dtype=int); n = a.size
    z = rng.normal(0, 1, n); z[0] = rng.normal(0, 1 / np.sqrt(1 - rho ** 2))
    e = lfilter([1.0], [1.0, -rho], z)
    return a, mu * a + e


def curve(Es=(5, 10, 20, 50, 100, 200), Lc=20, rho=0.9, mu=2.0, thr=2.0, R=400, B=300, seed=0):
    sd = 1.0 / np.sqrt(1 - rho ** 2)
    true_recall = float(1 - norm.cdf((thr - mu) / sd))
    rng = np.random.default_rng(seed); rows = []
    for E in Es:
        hit = {"naive": [], "ess": [], "mbb": [], "episode": []}
        for _ in range(R):
            a, s = make_series(E, Lc, rho=rho, mu=mu, rng=rng)
            hits = (s[a == 1] > thr).astype(float)
            _, lo, hi = C.naive_normal_ci(hits); hit["naive"].append(lo <= true_recall <= hi)
            _, lo, hi, _ = C.ess_plugin_ci(hits); hit["ess"].append(lo <= true_recall <= hi)
            _, lo, hi, *_ = C.block_bootstrap_ci(a, s, C.recall_at_threshold(thr), B=B, rng=rng, kind="basic")
            hit["mbb"].append((not np.isnan(lo)) and lo <= true_recall <= hi)
            _, lo, hi, ne, _ = C.episode_bootstrap_ci(a, s, C.recall_at_threshold(thr), B=B, rng=rng, kind="basic")
            hit["episode"].append((not np.isnan(lo)) and lo <= true_recall <= hi)
        row = {"E_attack": E, "n_attack": E * Lc, "true_recall": round(true_recall, 3)}
        for k, v in hit.items():
            p = float(np.mean(v)); row[f"cov_{k}"] = round(p, 3); row[f"se_{k}"] = round(np.sqrt(p * (1 - p) / R), 3)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--R", type=int, default=400); ap.add_argument("--B", type=int, default=300)
    a = ap.parse_args()
    df = curve(R=a.R, B=a.B)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    df.to_csv("diagnostics/p13_episode.csv", index=False)
