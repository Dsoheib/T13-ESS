"""P35: is the CICIDS2017 flow-grain DIF genuine serial dependence, five-tuple CLUSTERING, or a
sub-minute ordering artifact? Three-way comparison on Wednesday benign flows, per feature:
  (a) as-shipped ROW order
  (b) within-minute order RANDOMISED (stable sort by minute, shuffle inside each minute), R>=20
      -> if DIF collapses toward 1, the dependence is a sub-minute ordering artifact
  (c) DEDUP five-tuple (keep first flow per Flow ID) -> if DIF collapses, it is five-tuple
      CLUSTERING (clustered, not serial -> parent becomes Obuchowski, not Kunsch)
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.dif import integrated_autocorrelation_time as tau

FEATS = ["Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Bwd Packet Length Mean"]


def load(path, cap):
    d = pd.read_csv(path, low_memory=False, encoding="latin1"); d.columns = [c.strip() for c in d.columns]
    d = d[d["Label"].astype(str).str.upper() == "BENIGN"].reset_index(drop=True)
    d["min"] = pd.to_datetime(d["Timestamp"], errors="coerce", dayfirst=True).dt.floor("min")
    for c in FEATS:
        d[c] = pd.to_numeric(d[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = d.dropna(subset=[c for c in FEATS if c in d.columns] + ["min"]).reset_index(drop=True)
    return d.iloc[:cap].reset_index(drop=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--cap", type=int, default=67000); ap.add_argument("--R", type=int, default=20)
    a = ap.parse_args()
    d = load(a.csv, a.cap)
    feats = [c for c in FEATS if c in d.columns]
    n5 = d.drop_duplicates(subset=["Flow ID"]).shape[0]
    print(f"benign flows n={len(d)}  unique five-tuples(Flow ID)={n5}  ({n5/len(d):.1%})")
    rng = np.random.default_rng(0); rows = []
    # group indices by minute for shuffle
    groups = [g.to_numpy() for _, g in d.groupby("min").indices.items()] if False else None
    minute_index = {m: np.array(idx) for m, idx in d.groupby("min").indices.items()}
    order_by_min = np.concatenate([minute_index[m] for m in sorted(minute_index)])
    for c in feats:
        x = d[c].to_numpy()
        a_row = tau(x, "geyer", guard=False)[0]
        # (b) within-minute shuffle, R times
        bvals = []
        for _ in range(a.R):
            perm = np.concatenate([rng.permutation(minute_index[m]) for m in sorted(minute_index)])
            bvals.append(tau(x[perm], "geyer", guard=False)[0])
        bvals = np.array(bvals)
        # (c) dedup five-tuple, keep first occurrence (preserves row order)
        first = d.drop_duplicates(subset=["Flow ID"], keep="first")
        c_dedup = tau(first[c].to_numpy(), "geyer", guard=False)[0]
        rows.append({"feature": c, "DIF_row(a)": round(a_row, 1),
                     "DIF_minShuffle(b)_mean": round(bvals.mean(), 1), "b_sd": round(bvals.std(), 1),
                     "DIF_dedup5tuple(c)": round(c_dedup, 1), "n_dedup": len(first)})
    tab = pd.DataFrame(rows); pd.set_option("display.width", 200)
    print(tab.to_string(index=False))
    tab.to_csv("results/p35_order_confound.csv", index=False)
    print("\nInterpretation: (b)->~1 = sub-minute ordering artifact; (c)->~1 = five-tuple clustering "
          "(clustered, Obuchowski); both stay high = genuine serial dependence (Kunsch).")
