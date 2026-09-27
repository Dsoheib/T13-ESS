"""AAL MQTT-bridge telemetry DIF (paper section 3.4, self-application). No acquisition needed.
Window-grain features with ISO window_start_time. Reports, for the BENIGN stream, the DIF of the
label sequence and each numeric feature, with segment CI and Geyer/batch agreement. The floor
guard (EstimatorFloorError) will fire on any series whose order is not genuine.
Usage: python3 scripts/aal_dif.py <labeled_csv>
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.dif import dif_report, dif_ci, EstimatorFloorError

DROP = {"label", "attack_type", "window_start_time", "window_end_time"}


def load(path):
    d = pd.read_csv(path)
    d["t"] = pd.to_datetime(d["window_start_time"], utc=True, errors="coerce")
    d = d.dropna(subset=["t"]).sort_values("t").reset_index(drop=True)
    feats = [c for c in d.columns if c not in DROP and c != "t" and np.issubdtype(d[c].dtype, np.number)]
    return d, feats


def time_order(d):
    ts = d["t"].astype("int64").to_numpy() / 1e9; dts = np.diff(ts)
    return dict(n=len(d), frac_dt_le_0=round(float(np.mean(dts <= 0)), 4),
                unique_ts_frac=round(len(np.unique(ts)) / len(ts), 4),
                dup_row_rate=round(1 - len(d.drop_duplicates()) / len(d), 4))


def dif_row(grain, family, series, x):
    try:
        rep = dif_report(x); t0, lo, hi, ok = dif_ci(x)
        return {"dataset": "AAL-MQTT-bridge", "grain": grain, "family": family, "series": series,
                "n": rep["n"], "dif_geyer": round(rep["dif_geyer"], 2), "dif_batch": round(rep["dif_batch"], 2),
                "dif_ci_lo": round(lo, 2), "dif_ci_hi": round(hi, 2), "dif_ci_reliable": ok,
                "n_eff_geyer": round(rep["n_eff_geyer"], 1), "reliable": rep["rel_reliable"], "agree": rep["agree"]}
    except EstimatorFloorError as e:
        return {"dataset": "AAL-MQTT-bridge", "grain": grain, "family": family, "series": series,
                "n": len(x), "dif_geyer": "FLOOR_GUARD", "dif_batch": None, "dif_ci_lo": None,
                "dif_ci_hi": None, "dif_ci_reliable": False, "n_eff_geyer": None, "reliable": False, "agree": False}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv", nargs="?", default="../bridgeguard_features/features_labeled.csv")
    a = ap.parse_args()
    d, feats = load(a.csv)
    print("time-order audit:", time_order(d))
    ben = d[d["label"] == 0].reset_index(drop=True)
    print(f"n_windows={len(d)} benign={len(ben)} prevalence(attack)={1-ben.shape[0]/d.shape[0]:.3f}")
    rows = [dif_row("window", "label", "y", d["label"].values.astype(float))]
    for c in feats:
        b = ben[c].values
        if np.nanstd(b) > 0 and b.size > 100:
            rows.append(dif_row("window", "feature", f"{c}|benign", b))
    tab = pd.DataFrame(rows)
    pd.set_option("display.width", 200); pd.set_option("display.max_rows", 60)
    print(tab.to_string(index=False))
    # H2 read at window grain: median benign-feature DIF
    fb = tab[(tab.family == "feature") & (tab.dif_geyer != "FLOOR_GUARD")]
    if len(fb):
        med = float(np.median(pd.to_numeric(fb.dif_geyer)))
        print(f"\nBENIGN-feature median DIF (window grain) = {med:.2f}  "
              f"[H2: >=2 supports; <1.5 void] ; features with DIF>=2: {(pd.to_numeric(fb.dif_geyer)>=2).sum()}/{len(fb)}")
    import os
    if os.path.exists("results/dif_by_dataset.csv") and os.path.getsize("results/dif_by_dataset.csv") > 0:
        old = pd.read_csv("results/dif_by_dataset.csv"); tab = pd.concat([old[old.dataset != "AAL-MQTT-bridge"], tab], ignore_index=True)
    tab.to_csv("results/dif_by_dataset.csv", index=False); print("\nwritten results/dif_by_dataset.csv")
