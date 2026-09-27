"""CICIDS2017 GeneratedLabelledFlows DIF (H2 measurement on genuine flow data).
Time-order audit of the shipped Timestamp, then flow- and window-grain DIF of the benign stream
and reference-detector scores, plus differential DIF on one detector pair. Uses as-shipped ROW
order as the sequence (CICFlowMeter writes flows in ~capture order); the Timestamp audit is
reported beside it (CICIDS2017's afternoon timestamps are 12h without AM/PM -> a documented
integrity caveat).
Usage: python3 scripts/cicids_dif.py "<path to day CSV>" --cap 150000
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.dif import dif_report, dif_ci, integrated_autocorrelation_time, EstimatorFloorError
from t13.datasets import to_grain, reference_scores

FEATS = ["Flow Duration", "Total Fwd Packets", "Flow Bytes/s", "Flow Packets/s",
         "Flow IAT Mean", "Fwd Packet Length Mean", "Bwd Packet Length Mean"]


def load(path, cap):
    d = pd.read_csv(path, low_memory=False, encoding="latin1"); d.columns = [c.strip() for c in d.columns]
    d["y"] = (d["Label"].astype(str).str.upper() != "BENIGN").astype(int)
    d["row"] = np.arange(len(d))                       # as-shipped capture order
    ts = pd.to_datetime(d["Timestamp"], errors="coerce", dayfirst=True)
    d["_ts"] = ts.astype("int64") / 1e9
    feats = [c for c in FEATS if c in d.columns]
    for c in feats:
        d[c] = pd.to_numeric(d[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
    d = d.dropna(subset=feats).reset_index(drop=True)
    if len(d) > cap:
        d = d.iloc[:cap].reset_index(drop=True)          # contiguous prefix in capture order
    return d, feats


def audit_ts(d):
    ts = d["_ts"].to_numpy(); ok = ~np.isnan(ts); ts = ts[ok]; dts = np.diff(ts)
    return dict(frac_dt_le_0_rowlorder=round(float(np.mean(dts <= 0)), 4) if dts.size else None,
                unique_ts_frac=round(len(np.unique(ts)) / len(ts), 4) if ts.size else None,
                dup_row_rate=round(1 - len(d.drop_duplicates()) / len(d), 4))


def difrow(grain, family, series, x):
    try:
        rep = dif_report(x); _, lo, hi, ok = dif_ci(x)
        return {"dataset": "CICIDS2017-Wed", "grain": grain, "family": family, "series": series,
                "n": rep["n"], "dif_geyer": round(rep["dif_geyer"], 2), "dif_batch": round(rep["dif_batch"], 2),
                "dif_ci_lo": round(lo, 2), "dif_ci_hi": round(hi, 2), "reliable": rep["rel_reliable"], "agree": rep["agree"]}
    except EstimatorFloorError:
        return {"dataset": "CICIDS2017-Wed", "grain": grain, "family": family, "series": series,
                "n": len(x), "dif_geyer": "FLOOR_GUARD", "dif_batch": None, "dif_ci_lo": None, "dif_ci_hi": None, "reliable": False, "agree": False}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--cap", type=int, default=150000); ap.add_argument("--fpr", type=float, default=0.01)
    a = ap.parse_args()
    d, feats = load(a.csv, a.cap)
    print("time-order audit (Timestamp in as-shipped row order):", audit_ts(d))
    print(f"n={len(d)} benign={int((d.y==0).sum())} attack={int((d.y==1).sum())} features={feats}")
    ben = d[d.y == 0].reset_index(drop=True)
    rows = [difrow("flow", "label", "y", d["y"].values.astype(float))]
    for c in feats:                                        # flow grain, benign stream, capture order
        rows.append(difrow("flow", "feature", f"{c}|benign", ben[c].values))
    # window grain: 60s bins by timestamp (best-effort given the AM/PM caveat)
    dw = d.assign(t=d["_ts"]).dropna(subset=["t"])
    if len(dw) > 400:
        g = (dw["t"] // 60).astype(int); wb = dw.groupby(g)
        wfeat = wb[feats].mean(); wy = wb["y"].max()
        for c in feats:
            b = wfeat.loc[wy.values == 0, c].dropna().values
            if b.size > 100:
                rows.append(difrow("window:60s", "feature", f"{c}|benign", b))
    # detector scores + alarm indicator (flow grain), and differential DIF on a pair
    diff_rows = []
    if len(d) > 400:
        dord = d.assign(t=d["row"])                       # capture order for temporal split
        scores = reference_scores(dord, feats, fpr=a.fpr)
        n = len(dord) // 2; yte = dord["y"].to_numpy(int)[n:]
        for name, (yv, sv) in scores.items():
            benv = sv[yv == 0]
            if benv.size > 200:
                rows.append(difrow("flow", "detector", f"{name}|score(benign)", benv))
                thr = np.quantile(benv, 1 - a.fpr)
                rows.append(difrow("flow", "detector", f"{name}|alarm@{a.fpr}", (benv > thr).astype(float)))
        names = list(scores); losses = {}
        for nm, (yv, sv) in scores.items():
            thr = np.quantile(sv[yv == 0], 1 - a.fpr); losses[nm] = (((sv > thr).astype(int)) != yv).astype(float)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                A, Bn = names[i], names[j]; dt = losses[A] - losses[Bn]
                if np.std(dt) > 0:
                    try:
                        t0 = integrated_autocorrelation_time(dt, "geyer")[0]; _, lo, hi, ok = dif_ci(dt)
                    except EstimatorFloorError:
                        t0, lo, hi, ok = "FLOOR_GUARD", None, None, False
                    sA = integrated_autocorrelation_time(scores[A][1][scores[A][0] == 0], "geyer", guard=False)[0]
                    diff_rows.append({"pair": f"{A}-{Bn}", "dif_diff": t0 if isinstance(t0, str) else round(t0, 2),
                                      "dif_diff_ci": None if lo is None else f"[{lo:.2f},{hi:.2f}]",
                                      "dif_stream_A_benign": round(sA, 2),
                                      "mean_loss_diff": round(dt.mean(), 4)})
    tab = pd.DataFrame(rows); pd.set_option("display.width", 200); pd.set_option("display.max_rows", 80)
    print(tab.to_string(index=False))
    fb = tab[(tab.family == "feature") & (tab.grain == "flow") & (tab.dif_geyer != "FLOOR_GUARD")]
    if len(fb):
        med = float(np.median(pd.to_numeric(fb.dif_geyer)))
        print(f"\nFLOW-grain benign-feature median DIF = {med:.2f}  [H2: >=2 supports; <1.5 void]; >=2: {(pd.to_numeric(fb.dif_geyer)>=2).sum()}/{len(fb)}")
    print("\n=== differential DIF ==="); print(pd.DataFrame(diff_rows).to_string(index=False))
    import os
    if os.path.exists("results/dif_by_dataset.csv") and os.path.getsize("results/dif_by_dataset.csv") > 0:
        old = pd.read_csv("results/dif_by_dataset.csv"); tab = pd.concat([old[old.dataset != "CICIDS2017-Wed"], tab], ignore_index=True)
    tab.to_csv("results/dif_by_dataset.csv", index=False)
    pd.DataFrame(diff_rows).to_csv("results/differential_dif.csv", index=False)
    print("\nwritten results/dif_by_dataset.csv + differential_dif.csv")
