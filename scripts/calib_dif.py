"""Calibration DIF on two NAMED datasets, declared EXCLUDED from the confirmatory corpus:
TON_IoT-Fridge and TON_IoT-Weather (real, time-ordered IoT telemetry: date+time, label).

Reports, per dataset:
  - stream DIF (+ segment CI) for the label sequence, each benign feature, and the benign-only
    detector-score sequences (the series that governs FPR intervals);
  - the ALARM-indicator DIF at 1% FPR;
  - the DIFFERENTIAL DIF: tau_int of the paired loss-difference d_t = loss_A - loss_B for a
    detector pair (the quantity that governs a Diebold-Mariano / "A beats B" test). If the
    differential DIF is < 1.5 where the stream DIF is >= 2, inflating a reported SE by
    sqrt(stream DIF) OVER-corrects, and H3b's summary-only survival arm must be dropped.

Usage: python3 scripts/calib_dif.py <name> <csv> --cap 120000
"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from t13.dif import dif_report, dif_ci, integrated_autocorrelation_time
from t13.datasets import reference_scores, to_grain


def load_toniot(path, cap):
    d = pd.read_csv(path, low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    dt = pd.to_datetime(d["date"].astype(str).str.strip() + " " + d["time"].astype(str).str.strip(),
                        format="%d-%b-%y %H:%M:%S", errors="coerce")
    d = d.assign(t=dt.astype("int64") / 1e9, y=pd.to_numeric(d["label"], errors="coerce"))
    drop = {"date", "time", "label", "type", "t", "y"}
    feats = []
    for c in [c for c in d.columns if c not in drop]:
        col = pd.to_numeric(d[c], errors="coerce")
        if col.notna().mean() > 0.9:      # keep only genuinely numeric features
            d[c] = col; feats.append(c)
    d = d.dropna(subset=["t", "y"]).sort_values("t").reset_index(drop=True)
    d = d.dropna(subset=feats).reset_index(drop=True)
    # pick the most class-balanced CONTIGUOUS (time-ordered) window of size cap, so a detector
    # pair can be fit; contiguity preserves the within-window serial dependence we measure.
    y = d["y"].to_numpy(int); n = len(d)
    if n > cap:
        step = max(1, cap // 4); best_i, best_bal = 0, -1.0
        for i in range(0, n - cap + 1, step):
            p = y[i:i + cap].mean(); bal = min(p, 1 - p)
            if bal > best_bal:
                best_bal, best_i = bal, i
        d = d.iloc[best_i:best_i + cap].reset_index(drop=True)
    return d, feats


def _ci_row(name, grain, family, series, x):
    rep = dif_report(x); t0, lo, hi, ok = dif_ci(x)
    return {"dataset": name, "grain": grain, "family": family, "series": series, "n": rep["n"],
            "dif_geyer": round(rep["dif_geyer"], 1), "dif_batch": round(rep["dif_batch"], 1),
            "dif_ci_lo": round(lo, 1), "dif_ci_hi": round(hi, 1), "dif_ci_reliable": ok,
            "n_eff_geyer": round(rep["n_eff_geyer"], 1), "reliable": rep["rel_reliable"],
            "agree": rep["agree"]}


def run(name, csv, cap=120000, fpr=0.01):
    d, feats = load_toniot(csv, cap)
    print(f"{name}: {len(d)} rows, prevalence {d.y.mean():.4f}, features {feats}")
    rows = [_ci_row(name, "flow", "label", "y", d["y"].values)]
    for c in feats:
        b = d.loc[d.y == 0, c].values
        if b.size > 200:
            rows.append(_ci_row(name, "flow", "feature", f"{c}|benign", b))
    diff_rows = []
    if len(d) > 400 and len(feats) >= 1:
        scores = reference_scores(d, feats, fpr=fpr)
        n = len(d) // 2; yte = d["y"].to_numpy(int)[n:]
        for det, (yv, sv) in scores.items():
            ben = sv[yv == 0]
            if ben.size > 200:
                rows.append(_ci_row(name, "flow", "detector", f"{det}|score(benign)", ben))
                thr = np.quantile(ben, 1 - fpr)
                rows.append(_ci_row(name, "flow", "detector", f"{det}|alarm@{fpr}", (ben > thr).astype(float)))
        # differential DIF for detector pairs (paired 0/1 loss at 1% FPR operating point)
        names = list(scores)
        losses = {}
        for det, (yv, sv) in scores.items():
            thr = np.quantile(sv[yv == 0], 1 - fpr)
            losses[det] = (((sv > thr).astype(int)) != yv).astype(float)  # 0/1 error in time order
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                A, Bn = names[i], names[j]
                d_t = losses[A] - losses[Bn]
                tau_stream_A = integrated_autocorrelation_time(scores[A][1][scores[A][0] == 0], "geyer")[0]
                t0, lo, hi, ok = dif_ci(d_t) if np.std(d_t) > 0 else (1.0, 1.0, 1.0, False)
                diff_rows.append({"dataset": name, "pair": f"{A}-{Bn}",
                                  "dif_diff_geyer": round(integrated_autocorrelation_time(d_t, "geyer")[0], 2),
                                  "dif_diff_ci_lo": round(lo, 2), "dif_diff_ci_hi": round(hi, 2),
                                  "dif_stream_A_benign": round(tau_stream_A, 2),
                                  "mean_loss_A": round(losses[A].mean(), 4), "mean_loss_B": round(losses[Bn].mean(), 4),
                                  "mean_loss_diff": round(d_t.mean(), 4)})
    return pd.DataFrame(rows), pd.DataFrame(diff_rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("name"); ap.add_argument("csv")
    ap.add_argument("--cap", type=int, default=120000); a = ap.parse_args()
    tab, diff = run(a.name, a.csv, a.cap)
    pd.set_option("display.width", 220)
    print("\n=== stream DIF ==="); print(tab.to_string(index=False))
    print("\n=== differential DIF ==="); print(diff.to_string(index=False))
    import os
    for path, df in [("results/dif_by_dataset.csv", tab), ("results/differential_dif.csv", diff)]:
        if os.path.exists(path) and os.path.getsize(path) > 0 and not df.empty:
            try:
                old = pd.read_csv(path); df = pd.concat([old[old.dataset != a.name], df], ignore_index=True)
            except Exception:
                pass
        if not df.empty:
            df.to_csv(path, index=False)
    print(f"\nappended {a.name} to results/dif_by_dataset.csv and results/differential_dif.csv")
