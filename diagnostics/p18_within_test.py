"""P18: is the random-split naive interval's better coverage because the correction is
impossible (shuffling defeats it) or because the random test set is genuinely LESS dependent
(neighbours split across the partition)?

For each split we report two tau_hat of the benign score sequence (the series that governs FPR):
  tau_true_order : test members placed back in their ORIGINAL time order (the real within-test
                   dependence, regardless of what the analyst sees)
  tau_seen_order : the order the interval constructor actually sees
                   (temporal: same as original; random: shuffled -> ~1)
If tau_true_order(random) ~= 1, the random test set is genuinely easier (drift-lit finding by
another route). If tau_true_order(random) stays large while tau_seen_order ~= 1, shuffling is
merely hiding real dependence and the correction is being defeated.
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.sim import generate, SCENARIOS
from t13.dif import integrated_autocorrelation_time as tau


def run(scenario="bg_ar__lab_campaign", n=5000, R=300, fpr=0.01, seed=0):
    kw = SCENARIOS[scenario]; rng = np.random.default_rng(seed); rows = []
    for split in ("temporal", "random"):
        true_o, seen_o = [], []
        for _ in range(R):
            a, s = generate(2 * n, rng=rng, **kw)
            if split == "random":
                perm = rng.permutation(2 * n)
                a_s, s_s = a[perm], s[perm]                       # shuffled (what analyst sees)
                te_idx = perm[n:]                                 # original positions in test
                order = np.sort(te_idx)                           # restore original time order
                b_true = s[order][a[order] == 0]                  # benign scores, original order
                b_seen = s_s[n:][a_s[n:] == 0]                    # benign scores, shuffled order
            else:
                b_true = s[n:][a[n:] == 0]; b_seen = b_true
            if b_true.size >= 3:
                true_o.append(tau(b_true, "geyer")[0])
            if b_seen.size >= 3:
                seen_o.append(tau(b_seen, "geyer")[0])
        rows.append({"split": split,
                     "tau_true_order": round(float(np.mean(true_o)), 2),
                     "tau_seen_order": round(float(np.mean(seen_o)), 2)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=5000); ap.add_argument("--R", type=int, default=300)
    a = ap.parse_args()
    df = run(n=a.n, R=a.R)
    print(df.to_string(index=False)); df.to_csv("diagnostics/p18_within_test.csv", index=False)
