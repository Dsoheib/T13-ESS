"""Adapter for CIC-format flow CSVs (CICIDS2017/2018, CICIoT2023, CICIoMT2024, CICDDoS2019).
Time order: the ' Timestamp' / 'Timestamp' column (flow START time, per CICFlowMeter). Files are
per-day; concatenate in day order. Bidirectional flows overlap; ordering by start time is the
primary choice, by (start + duration) the sensitivity ordering (column t_end).
Label: 'Label' == 'BENIGN' (case-insensitive) -> 0 else 1.
Usage: python3 data/order/cic_csv.py file1.csv [file2.csv ...] --out data/order/cicids2017_ordered.csv --cap 300000
"""
import argparse, pandas as pd, numpy as np

p = argparse.ArgumentParser(); p.add_argument("files", nargs="+"); p.add_argument("--out", required=True)
p.add_argument("--cap", type=int, default=300_000, help="keep a CONTIGUOUS prefix after sorting (not a random sample)")
p.add_argument("--features", nargs="*", default=["Flow Duration", "Tot Fwd Pkts", "Flow Byts/s", "Flow Pkts/s", "Flow IAT Mean"])
a = p.parse_args()
frames = []
for f in a.files:
    d = pd.read_csv(f, low_memory=False); d.columns = [c.strip() for c in d.columns]
    ts = pd.to_datetime(d["Timestamp"], errors="coerce", dayfirst=True)
    d = d.assign(t=ts.astype("int64") / 1e9, y=(d["Label"].astype(str).str.upper() != "BENIGN").astype(int))
    dur = pd.to_numeric(d.get("Flow Duration", 0), errors="coerce").fillna(0) / 1e6
    d["t_end"] = d["t"] + dur
    keep = ["t", "t_end", "y"] + [c for c in a.features if c in d.columns]
    frames.append(d[keep])
df = pd.concat(frames).dropna(subset=["t"]).sort_values("t").reset_index(drop=True)
for c in df.columns:
    if c not in ("t", "t_end", "y"):
        df[c] = pd.to_numeric(df[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
df = df.dropna().iloc[: a.cap]
df.to_csv(a.out, index=False)
print(f"{len(df)} rows, prevalence {df.y.mean():.4f}, span {df.t.max()-df.t.min():.0f}s -> {a.out}")
print("TIME ORDER: recovered from flow start timestamps (CICFlowMeter). Sensitivity ordering: t_end.")
