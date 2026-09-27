"""Producer for results/cicids_flow_dif.csv (P100): the within-minute-shuffle (b) flow-grain DIF
headline with the as-shipped (a) value beside it, per benign feature per day, from the raw CICIDS2017
GeneratedLabelledFlows daily CSVs. Previously this file was hand-assembled and had no producer; this
script regenerates it deterministically (seeded shuffles). Requires the raw daily CSVs fetched by
scripts/fetch_raw.py (not redistributed). Run via `make realdata`.

Schema: day,feature,dif_b_headline,dif_b_batch,dif_b_sd,dif_a_asshipped,n_b,n_eff_b,estimable
dif_b_headline is the (b) within-minute-shuffle Geyer DIF; dif_b_batch is the batch-means DIF on the
same shuffle, so the agreement rule (P99) can be applied to the (b) cells (P106). n_eff_b is the
CONSERVATIVE n_eff = n / max(geyer, batch) (P108). Emits dif_a_asshipped (never "upperbound", P91).
Usage: python3 scripts/flow_dif_producer.py <data_dir>   # dir with Monday/Tuesday/Wednesday *.csv
"""
import sys, os, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.dif import integrated_autocorrelation_time as tau

FEATS = ["Flow Duration", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Bwd Packet Length Mean"]
DAYS = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday"}
NEFF_FLOOR = 50
R_SHUFFLE = 50
# CICIDS2017 afternoon timestamps are 12h without AM/PM, so afternoon minutes collide with morning
# ones; the within-minute shuffle is only valid on the AM/PM-unambiguous MORNING window. CAP restricts
# to the first CAP benign flows (morning), matching the established (b) methodology (P37/P40, p35).
CAP = 67000


def dif(x, rule):
    return float(tau(x, rule, guard=False)[0])


def day_rows(day_key, path, rng):
    d = pd.read_csv(path, low_memory=False, encoding="latin1")
    d.columns = [c.strip() for c in d.columns]
    d = d[d["Label"].astype(str).str.upper() == "BENIGN"].copy()
    ts = pd.to_datetime(d["Timestamp"], errors="coerce", dayfirst=True)
    d["min"] = ts.dt.floor("min")                              # minute bucket (morning, unambiguous)
    for c in FEATS:
        d[c] = pd.to_numeric(d.get(c), errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = d.dropna(subset=[c for c in FEATS if c in d.columns] + ["min"]).reset_index(drop=True)
    d = d.iloc[:CAP].reset_index(drop=True)                    # AM/PM-unambiguous morning window
    minute_index = {m: np.array(idx) for m, idx in d.groupby("min").indices.items()}
    order = sorted(minute_index)
    rows = []
    for c in FEATS:
        if c not in d.columns:
            continue
        x = d[c].to_numpy(); n = len(x)
        a_row = dif(x, "geyer")                                # (a) as-shipped Geyer
        bg, bb = [], []
        for _ in range(R_SHUFFLE):                             # (b) within-minute shuffle, both estimators
            xs = x[np.concatenate([rng.permutation(minute_index[m]) for m in order])]
            bg.append(dif(xs, "geyer")); bb.append(dif(xs, "batch"))
        b_geyer, b_batch = float(np.mean(bg)), float(np.mean(bb))
        n_eff_b = n / max(b_geyer, b_batch) if max(b_geyer, b_batch) > 0 else np.nan   # conservative
        rows.append(dict(day=day_key, feature=c, dif_b_headline=round(b_geyer, 1),
                         dif_b_batch=round(b_batch, 1), dif_b_sd=round(float(np.std(bg)), 1),
                         dif_a_asshipped=round(a_row, 1), n_b=int(n),
                         n_eff_b=round(n_eff_b, 1), estimable=bool(n_eff_b >= NEFF_FLOOR)))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("data_dir")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    rows = []
    for key, name in DAYS.items():
        hits = [f for f in os.listdir(a.data_dir) if name in f and f.endswith(".csv")]
        if not hits:
            print(f"WARNING: no {name} CSV in {a.data_dir}; skipping", file=sys.stderr); continue
        rows += day_rows(key, os.path.join(a.data_dir, hits[0]), rng)
    out = pd.DataFrame(rows)
    out.to_csv("results/cicids_flow_dif.csv", index=False)
    print(out.to_string(index=False)); print("\nwrote results/cicids_flow_dif.csv")
