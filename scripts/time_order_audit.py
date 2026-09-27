"""Time-order integrity audit (P21/P22 prerequisite). For every candidate dataset:
  has_timestamp, n_rows, frac_dt_le_0 (consecutive Δt<=0 in SHIPPED order),
  unique_ts_frac, dup_full_row_rate -> verdict.
A dataset that fails is reported as TIME ORDER UNRECOVERABLE and excluded from H2.
Writes results/time_order_audit.csv. Datasets not on disk are recorded as NOT_ACQUIRED so the
audit population is explicit.
Usage: python3 scripts/time_order_audit.py
"""
import sys, os, glob; sys.path.insert(0, "src")
import numpy as np, pandas as pd


def audit_toniot(path):
    d = pd.read_csv(path, low_memory=False); d.columns = [c.strip() for c in d.columns]
    dt = pd.to_datetime(d["date"].astype(str).str.strip() + " " + d["time"].astype(str).str.strip(),
                        format="%d-%b-%y %H:%M:%S", errors="coerce")
    ts = dt.astype("int64").to_numpy() / 1e9
    dts = np.diff(ts)
    return dict(has_timestamp=True, n_rows=len(d), frac_dt_le_0=round(float(np.mean(dts <= 0)), 4),
                unique_ts_frac=round(len(np.unique(ts)) / len(ts), 4),
                dup_full_row_rate=round(1 - len(d.drop_duplicates()) / len(d), 4))


def audit_cic_no_ts(path):
    d = pd.read_csv(path, low_memory=False, nrows=200000); d.columns = [c.strip() for c in d.columns]
    has_ts = any(c.lower() in ("timestamp", "flow start", "flow_start", "stime", "ts") for c in d.columns)
    return dict(has_timestamp=has_ts, n_rows=len(d), frac_dt_le_0=np.nan, unique_ts_frac=np.nan,
                dup_full_row_rate=round(1 - len(d.drop_duplicates()) / len(d), 4))


def verdict(m):
    if not m.get("has_timestamp"):
        return "UNRECOVERABLE (no timestamp column)"
    if m["frac_dt_le_0"] > 0.01:
        return f"UNRECOVERABLE (non-monotone: {m['frac_dt_le_0']:.0%} of consecutive pairs Δt<=0)"
    if m["dup_full_row_rate"] > 0.05 or m["unique_ts_frac"] < 0.5:
        return f"FLAG (dup_rows={m['dup_full_row_rate']:.0%}, unique_ts={m['unique_ts_frac']:.0%})"
    return "RECOVERABLE"


BASE = ".."
CANDIDATES = [
    ("TON_IoT-Fridge",  f"{BASE}/toniot_data/IoT_Fridge.csv",  audit_toniot),
    ("TON_IoT-Weather", f"{BASE}/toniot_data/IoT_Weather.csv", audit_toniot),
    ("CICIoMT2024-Benign", f"{BASE}/downloads/Benign_test.pcap.csv", audit_cic_no_ts),
    ("CICIoMT2024-ARPspoof", f"{BASE}/downloads/ARP_Spoofing_test.pcap.csv", audit_cic_no_ts),
]
NOT_ON_DISK = ["CICIDS2017", "CICIDS2018", "CICIoT2023", "UNSW-NB15", "MAWIFlow", "Edge-IIoTset"]

if __name__ == "__main__":
    rows = []
    for name, path, fn in CANDIDATES:
        if os.path.exists(path):
            m = fn(path); m.update(dataset=name, verdict=verdict(m))
        else:
            m = dict(dataset=name, has_timestamp=None, n_rows=0, verdict="NOT_ACQUIRED")
        rows.append(m)
    for name in NOT_ON_DISK:
        rows.append(dict(dataset=name, has_timestamp=None, n_rows=0, verdict="NOT_ACQUIRED (needs download)"))
    df = pd.DataFrame(rows)[["dataset", "has_timestamp", "n_rows", "frac_dt_le_0", "unique_ts_frac", "dup_full_row_rate", "verdict"]]
    df.to_csv("results/time_order_audit.csv", index=False)
    pd.set_option("display.width", 200); print(df.to_string(index=False))
