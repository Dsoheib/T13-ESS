"""Packet-grain DIF from a mid-file PCAPNG byte-range chunk (P41: non-adjacent windows across the
day). The capture is pcapng (magic 0a0d0d0a). We RESYNC on Enhanced Packet Blocks (type 6): a
block carries its total length at BOTH ends, so a candidate offset is validated when
block_type==6, btl%4==0, and the trailing length matches — then confirmed over a run of blocks.
Timestamp assumed microsecond resolution (pcapng default). Extract (ts, orig_len) and compute
inter-arrival / packet-size / packets-per-second DIF.
Usage: python3 scripts/pcap_window_dif.py <chunk> <label>
"""
import sys, struct; sys.path.insert(0, "src")
import numpy as np
from t13.dif import integrated_autocorrelation_time as tau, EstimatorFloorError

EPOCH_LO, EPOCH_HI = 1_499_000_000, 1_500_400_000
EPB = 6


def _valid_run(buf, off, k=15):
    n = len(buf)
    for _ in range(k):
        if off + 32 > n:
            return False
        bt, btl = struct.unpack_from("<II", buf, off)
        if bt != EPB or btl < 32 or btl % 4 or off + btl > n:
            return False
        if struct.unpack_from("<I", buf, off + btl - 4)[0] != btl:
            return False
        th, tl, cap, orig = struct.unpack_from("<IIII", buf, off + 12)
        ts = ((th << 32) | tl) * 1e-6
        if not (EPOCH_LO <= ts <= EPOCH_HI and 0 < orig <= 65535):
            return False
        off += btl
    return True


def resync(buf):
    for off in range(0, min(len(buf), 8_000_000)):
        if struct.unpack_from("<I", buf, off)[0] == EPB and _valid_run(buf, off):
            return off
    return None


def extract(buf, off, maxpk=500000):
    n = len(buf); ts, sz = [], []
    while off + 32 <= n and len(ts) < maxpk:
        bt, btl = struct.unpack_from("<II", buf, off)
        if bt != EPB or btl < 32 or off + btl > n or struct.unpack_from("<I", buf, off + btl - 4)[0] != btl:
            break
        th, tl, cap, orig = struct.unpack_from("<IIII", buf, off + 12)
        ts.append(((th << 32) | tl) * 1e-6); sz.append(orig); off += btl
    return np.array(ts), np.array(sz, float)


def rep(name, x):
    x = np.asarray(x, float)
    try:
        g = tau(x, "geyer")[0]; b = tau(x, "batch")[0]
        return f"{name}: DIF_geyer={g:.1f} batch={b:.1f} n_eff={len(x)/g:.0f} agree={'Y' if max(g,b)/max(1e-9,min(g,b))<=2 else 'N'}"
    except EstimatorFloorError:
        return f"{name}: FLOOR_GUARD"


def row(window, span, series, x):
    """One packet_windows.csv row (window, length_s, series, dif_geyer, dif_batch, n_eff, flag)."""
    import pandas as pd
    try:
        g = float(tau(x, "geyer")[0]); b = float(tau(x, "batch")[0]); ne = len(x) / g if g > 0 else float("nan")
    except EstimatorFloorError:
        g, b, ne = float("nan"), float("nan"), float("nan")
    flag = ""
    if not np.isnan(ne) and ne < 50:
        flag = "underpowered"
    elif not (np.isnan(g) or np.isnan(b)) and max(g, b) / max(1e-9, min(g, b)) > 2 and series == "packet_size":
        flag = "estimator-disagree"
    return dict(window=window, length_s=int(round(span)), series=series,
                dif_geyer=round(g, 1), dif_batch=round(b, 1),
                n_eff=int(ne) if not np.isnan(ne) else None, flag=flag)


if __name__ == "__main__":
    import argparse, os
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("label")
    ap.add_argument("--csv", default=None, help="append rows to this CSV (producer mode for packet_windows.csv)")
    a = ap.parse_args()
    buf = open(a.path, "rb").read()
    off = resync(buf)
    if off is None:
        print(f"[{a.label}] resync FAILED"); sys.exit(0)
    ts, sz = extract(buf, off)
    span = ts[-1] - ts[0] if len(ts) else 0
    print(f"[{a.label}] resync@{off} packets={len(ts)} span={span:.1f}s start_epoch={ts[0]:.0f}")
    iat = np.diff(ts); iat = iat[iat >= 0]
    sec = np.floor(ts - ts[0]).astype(int)
    print("   ", rep("inter_arrival", iat)); print("   ", rep("packet_size", sz))
    print("   ", rep("packets_per_1s", np.bincount(sec).astype(float)))
    if a.csv:
        import pandas as pd
        rows = [row(a.label, span, "inter_arrival", iat),
                row(a.label, span, "packets_per_1s", np.bincount(sec).astype(float)),
                row(a.label, span, "packet_size", sz)]
        new = pd.DataFrame(rows)
        if os.path.exists(a.csv) and os.path.getsize(a.csv) > 0:
            old = pd.read_csv(a.csv); old = old[old.window != a.label]
            new = pd.concat([old, new], ignore_index=True)
        new.to_csv(a.csv, index=False); print(f"   appended {a.label} to {a.csv}")
