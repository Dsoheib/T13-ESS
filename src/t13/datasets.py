"""Real-data pipeline: from a time-ordered benchmark to the DIF table.

Adapter contract (data/order/<dataset>.py): return a DataFrame with columns
  t   : sortable time (numeric seconds or datetime),
  y   : 0/1 label,
  plus numeric feature columns.
Each adapter documents how time order was recovered (pcap timestamps, flow start time,
file order) or declares UNRECOVERABLE — reported, never skipped.

DIF is computed for three series families per grain:
  label        : the y sequence (governs prevalence-dependent metrics)
  feature      : each numeric column, full and benign-only
  detector     : score sequences of reference detectors fitted with a temporal split
                 (governs score-based metrics; DIF is detector-dependent, so we report a
                 small fixed panel: IsolationForest, LogisticRegression, RandomForest).
Ordering sensitivity: flows may be ordered by start or end time; both are reported when
both are available (columns t and t_end).
"""
from __future__ import annotations
import numpy as np, pandas as pd
from .dif import dif_report

REFERENCE_DETECTORS = ("iforest", "logreg", "rf")


def _to_seconds(t):
    if np.issubdtype(np.asarray(t).dtype, np.number):
        return np.asarray(t, float)
    return pd.to_datetime(t).astype("int64").to_numpy() / 1e9


def to_grain(df, grain):
    d = df.copy(); d["_ts"] = _to_seconds(d["t"]); d = d.sort_values("_ts").reset_index(drop=True)
    if grain == "flow":
        return d.drop(columns="_ts")
    if grain.startswith("window:"):
        sec = float(grain.split(":")[1]); key = np.floor(d["_ts"] / sec).astype(int)
        num = [c for c in d.columns if c not in ("t", "y", "_ts") and np.issubdtype(d[c].dtype, np.number)]
        g = d.groupby(key)
        out = g[num].mean(); out["y"] = g["y"].max(); out["t"] = g["_ts"].min()
        return out.reset_index(drop=True)
    raise ValueError(grain)


def reference_scores(d, features, fpr=0.01, rng=0):
    """Fit reference detectors on the first half (temporal split), score the second half.
    Returns dict name -> (y_test, scores_test)."""
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X = d[features].to_numpy(float); y = d["y"].to_numpy(int); n = len(d) // 2
    Xtr, Xte, ytr, yte = X[:n], X[n:], y[:n], y[n:]
    sc = StandardScaler().fit(Xtr[ytr == 0] if (ytr == 0).sum() > 10 else Xtr)
    Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    out = {}
    iso = IsolationForest(random_state=rng).fit(Xtr[ytr == 0] if (ytr == 0).sum() > 10 else Xtr)
    out["iforest"] = (yte, -iso.score_samples(Xte))
    if ytr.min() != ytr.max():
        out["logreg"] = (yte, LogisticRegression(max_iter=500).fit(Xtr, ytr).predict_proba(Xte)[:, 1])
        out["rf"] = (yte, RandomForestClassifier(n_estimators=100, random_state=rng, n_jobs=-1).fit(Xtr, ytr).predict_proba(Xte)[:, 1])
    return out


def dif_table(df, dataset, grains=("flow", "window:60"), columns=None, detectors=True, fpr=0.01):
    rows = []
    for grain in grains:
        d = to_grain(df, grain)
        cols = columns or [c for c in d.columns if c not in ("t", "y") and np.issubdtype(d[c].dtype, np.number)]
        rows.append({"dataset": dataset, "grain": grain, "family": "label", "series": "y", **dif_report(d["y"].values)})
        for c in cols:
            rows.append({"dataset": dataset, "grain": grain, "family": "feature", "series": c, **dif_report(d[c].values)})
            b = d.loc[d["y"] == 0, c].values
            if b.size > 100:
                rows.append({"dataset": dataset, "grain": grain, "family": "feature", "series": f"{c}|benign", **dif_report(b)})
        if detectors and cols and len(d) > 400:
            for name, (yte, s) in reference_scores(d, cols, fpr).items():
                rows.append({"dataset": dataset, "grain": grain, "family": "detector", "series": f"{name}|score", **dif_report(s)})
                ben = s[yte == 0]
                if ben.size > 100:
                    thr = np.quantile(ben, 1 - fpr)
                    rows.append({"dataset": dataset, "grain": grain, "family": "detector", "series": f"{name}|alarm@{fpr}", **dif_report((ben > thr).astype(float))})
    return pd.DataFrame(rows)
