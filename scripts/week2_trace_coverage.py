"""Week 2 — trace-driven coverage.

The background noise is a moving-block resample of a real Monday benign series,
standardized to mean 0 and sd 1. Labels are the paper's campaign chain
(p_stay=0.995, prevalence=0.05), drawn independently of the trace. The score is
mu * label + noise with mu=2, the same shift as the coverage simulation.

The threshold is frozen. It is the 0.99 quantile of benign scores on one
block-bootstrap draw of length 400,000, seed 12345. Replicates do not re-learn
it, so this cell does not include threshold-estimation variance. False-positive
and recall targets are the rates on that same long draw. A second draw, seed
12346, measures how far those rates move.

Primary series, named before this run: Monday Flow Duration. It is the
confound-robust series from the plan. Companion series, also named before this
run: Monday Flow Packets/s, the Monday flow series whose Geyer and batch-means
estimates already agree. Both use the as-shipped row order and the 67,000-flow
prefix from Week 1.

Block length is the paper's rule on the source trace: twice the Geyer
autocorrelation time, at least 2, at most n^(2/3). Blocks do not wrap.
Replicates are independent block resamples, not overlapping slices of the one
observed trace.

Gate, fixed before the run. ESS-Wilson false-positive coverage is near nominal
when its unconditional point estimate is at least 0.90 at both n=5000 and
n=20000. Below 0.90 at either size, the miss is the result. If the nominal-n
Wilson interval is also at least 0.90 at n=5000, the trace did not reproduce
undercoverage. R=500. Recall is scored on the same replicates. No AUC bootstrap
is run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from t13.ci import ess_plugin_ci, naive_normal_ci, wilson, wilson_ess_ci  # noqa: E402
from t13.dif import block_length, integrated_autocorrelation_time  # noqa: E402
from t13.sim import _mc_se, _try, markov_labels  # noqa: E402
from week1_metric_level import cic_dir, load_cicids  # noqa: E402

SERIES = ("Flow Duration", "Flow Packets/s")
PRIMARY = "Flow Duration"
MU = 2.0
P_STAY = 0.995
PREVALENCE = 0.05
FPR_TARGET = 0.01
N_POP = 400_000
R = 500
SIZES = (5000, 20000)
NOMINAL_FLOOR = 0.90
REF_SEED = 12345
REF_REPEAT_SEED = 12346


def standardize(x):
    x = np.asarray(x, float)
    sd = float(x.std())
    if not np.isfinite(sd) or sd == 0.0:
        raise ValueError("trace has no variation")
    return (x - x.mean()) / sd


def resample_trace(trace, n, L, rng):
    """Non-wrapping moving blocks from the source trace, concatenated to length n."""
    trace = np.asarray(trace, float)
    m = trace.size
    L = int(L)
    if L < 1 or L >= m:
        raise ValueError(f"block length {L} is not inside a trace of length {m}")
    n_blocks = int(np.ceil(n / L))
    starts = rng.integers(0, m - L + 1, size=n_blocks)
    idx = starts[:, None] + np.arange(L)[None, :]
    return trace[idx].ravel()[:n]


def draw_scores(trace, L, n, rng, mu=MU, p_stay=P_STAY, prevalence=PREVALENCE):
    noise = resample_trace(trace, n, L, rng)
    labels = markov_labels(n, p_stay, prevalence, rng)
    return labels, mu * labels + noise


def long_run_reference(trace, L, seed, n_pop=N_POP, fpr=FPR_TARGET):
    labels, scores = draw_scores(trace, L, n_pop, np.random.default_rng(seed))
    benign = scores[labels == 0]
    attack = scores[labels == 1]
    if benign.size < 10 or attack.size < 10:
        raise RuntimeError("reference draw has an empty class")
    thr = float(np.quantile(benign, 1.0 - fpr))
    return {
        "threshold": thr,
        "fpr": float(np.mean(benign > thr)),
        "recall": float(np.mean(attack > thr)),
        "n_benign": int(benign.size),
        "n_attack": int(attack.size),
    }


def rates_at_threshold(trace, L, thr, seed, n_pop=N_POP):
    labels, scores = draw_scores(trace, L, n_pop, np.random.default_rng(seed))
    benign = scores[labels == 0]
    attack = scores[labels == 1]
    return {
        "fpr": float(np.mean(benign > thr)),
        "recall": float(np.mean(attack > thr)),
    }


def coverage_run(trace, L, n, R, thr, truth, seed):
    rng = np.random.default_rng(seed)
    cells = {}
    alarm_tau = []
    for _ in range(R):
        labels, scores = draw_scores(trace, L, n, rng)
        alarms = (scores[labels == 0] > thr).astype(float)
        hits = (scores[labels == 1] > thr).astype(float)
        if alarms.size >= 3:
            alarm_tau.append(float(integrated_autocorrelation_time(alarms, "geyer", guard=False)[0]))
        _try(cells, "fpr|naiveWilson", lambda alarms=alarms: wilson(float(alarms.sum()), float(alarms.size))[1:], truth["fpr"])
        _try(cells, "fpr|ESS-Wilson", lambda alarms=alarms: wilson_ess_ci(alarms)[1:3], truth["fpr"])
        _try(cells, "recall|naiveNormal", lambda hits=hits: naive_normal_ci(hits)[1:], truth["recall"])
        _try(cells, "recall|ESS", lambda hits=hits: ess_plugin_ci(hits)[1:3], truth["recall"])
    rows = []
    for key, (ncomp, ccov, ucov) in cells.items():
        metric, interval = key.split("|")
        cu = ucov / R
        cc = (ccov / ncomp) if ncomp else np.nan
        rows.append({
            "metric": metric,
            "interval": interval,
            "n": n,
            "R": R,
            "cov_uncond": cu,
            "mc_se_uncond": _mc_se(cu, R),
            "cov_cond": cc,
            "mc_se_cond": _mc_se(cc, ncomp) if ncomp else np.nan,
            "comp_rate": ncomp / R,
            "n_computable": ncomp,
        })
    mean_tau = float(np.mean(alarm_tau)) if alarm_tau else np.nan
    return rows, mean_tau


def cell(cov, metric, interval):
    hit = cov[(cov["metric"] == metric) & (cov["interval"] == interval)]
    if hit.empty:
        return np.nan
    return float(hit["cov_uncond"].iloc[0])


def gate_verdict(ess_5000, ess_20000, naive_5000, floor=NOMINAL_FLOOR):
    """Pre-specified. Near nominal means unconditional coverage >= 0.90."""
    near = ess_5000 >= floor and ess_20000 >= floor
    naive_under = naive_5000 < floor
    if near and naive_under:
        return (
            "Gate 2 met: ESS-Wilson false-positive coverage is at least 0.90 "
            "at n=5000 and n=20000, and the nominal-n Wilson interval is below 0.90 at n=5000."
        )
    if near and not naive_under:
        return (
            "Gate 2 partial: ESS-Wilson is at least 0.90 at both sizes, and the nominal-n "
            "Wilson interval is also at least 0.90 at n=5000. This trace does not reproduce "
            "the undercoverage the correction is meant to repair."
        )
    return (
        "Gate 2 miss: ESS-Wilson unconditional false-positive coverage is below 0.90 "
        "at n=5000 or n=20000. The miss is the result."
    )


def trace_record(frame, feature):
    values = frame.loc[frame["y"] == 0, feature].to_numpy(float)
    z = standardize(values)
    geyer = float(integrated_autocorrelation_time(z, "geyer", guard=False)[0])
    batch = float(integrated_autocorrelation_time(z, "batch")[0])
    ratio = max(geyer, batch) / max(min(geyer, batch), 1e-12)
    return {
        "feature": feature,
        "trace": z,
        "n_trace": int(z.size),
        "n_attack_in_prefix": int(frame["y"].sum()),
        "dif_geyer": geyer,
        "dif_batch": batch,
        "geyer_batch_ratio": ratio,
        "agree": bool(ratio <= 2.0),
        "L": int(block_length(z)),
        "max_abs": float(np.max(np.abs(z))),
    }


def run_series(rec):
    trace, L = rec["trace"], rec["L"]
    ref = long_run_reference(trace, L, REF_SEED)
    repeat = rates_at_threshold(trace, L, ref["threshold"], REF_REPEAT_SEED)
    cov_rows = []
    taus = {}
    for n in SIZES:
        rows, mean_tau = coverage_run(
            trace, L, n, R, ref["threshold"], ref, seed=10_000 + n + (0 if rec["feature"] == PRIMARY else 100)
        )
        for row in rows:
            row["feature"] = rec["feature"]
            row["primary"] = rec["feature"] == PRIMARY
        cov_rows.extend(rows)
        taus[n] = mean_tau
        print(
            f"  {rec['feature']} n={n} "
            f"FPR ESS {cell(pd.DataFrame(rows), 'fpr', 'ESS-Wilson'):.3f} "
            f"naive {cell(pd.DataFrame(rows), 'fpr', 'naiveWilson'):.3f}",
            flush=True,
        )
    meta = {
        "feature": rec["feature"],
        "primary": rec["feature"] == PRIMARY,
        "n_trace": rec["n_trace"],
        "n_attack_in_prefix": rec["n_attack_in_prefix"],
        "dif_geyer": rec["dif_geyer"],
        "dif_batch": rec["dif_batch"],
        "geyer_batch_ratio": rec["geyer_batch_ratio"],
        "agree": rec["agree"],
        "L": rec["L"],
        "max_abs": rec["max_abs"],
        "threshold": ref["threshold"],
        "fpr_ref": ref["fpr"],
        "recall_ref": ref["recall"],
        "fpr_ref_repeat": repeat["fpr"],
        "recall_ref_repeat": repeat["recall"],
        "fpr_ref_gap": abs(ref["fpr"] - repeat["fpr"]),
        "recall_ref_gap": abs(ref["recall"] - repeat["recall"]),
        "mean_alarm_dif_n5000": taus[5000],
        "mean_alarm_dif_n20000": taus[20000],
        "mu": MU,
        "p_stay": P_STAY,
        "prevalence": PREVALENCE,
        "n_pop": N_POP,
        "R": R,
    }
    return cov_rows, meta


def write_gate(path, cov, meta):
    primary = cov[cov["feature"] == PRIMARY]
    ess5 = cell(primary[primary["n"] == 5000], "fpr", "ESS-Wilson")
    ess20 = cell(primary[primary["n"] == 20000], "fpr", "ESS-Wilson")
    naive5 = cell(primary[primary["n"] == 5000], "fpr", "naiveWilson")
    verdict = gate_verdict(ess5, ess20, naive5)
    lines = [
        "# Week 2 gate",
        "",
        verdict,
        "",
        f"Pre-specified floor: unconditional ESS-Wilson coverage >= {NOMINAL_FLOOR:.2f} at both sample sizes.",
        "The verdict uses the primary series, Monday Flow Duration.",
        "Threshold frozen from a length-400,000 block-bootstrap draw, seed 12345. R=500.",
        "Blocks are non-wrapping. Labels are the campaign chain, independent of the trace.",
        "",
        "## Reference",
        "",
    ]
    for _, r in meta.iterrows():
        lines.append(
            f"- {r['feature']}: Geyer {r['dif_geyer']:.2f}, batch {r['dif_batch']:.2f}, "
            f"agree {bool(r['agree'])}, L {int(r['L'])}, max |z| {r['max_abs']:.1f}. "
            f"Reference FPR {r['fpr_ref']:.4f} (repeat gap {r['fpr_ref_gap']:.4f}), "
            f"recall {r['recall_ref']:.4f} (repeat gap {r['recall_ref_gap']:.4f}). "
            f"Mean alarm-indicator DIF {r['mean_alarm_dif_n5000']:.2f} at n=5000, "
            f"{r['mean_alarm_dif_n20000']:.2f} at n=20000."
        )
    lines += [
        "",
        "## Reading",
        "",
        f"The primary miss is the n=5000 cell ({ess5:.3f}). At n=20000 the same ESS-Wilson interval covers at {ess20:.3f}. "
        f"The nominal-n interval covers at {naive5:.3f} at n=5000.",
        "A companion whose reference false-positive rate is far from 0.01 has its threshold on a tie. "
        "That cell does not test whether the correction repairs undercoverage.",
        "",
        "## Unconditional coverage",
        "",
    ]
    show = cov.copy()
    for _, r in show.sort_values(["primary", "feature", "n", "metric", "interval"], ascending=[False, True, True, True, True]).iterrows():
        lines.append(
            f"- {r['feature']} n={int(r['n'])} {r['metric']} {r['interval']}: "
            f"{r['cov_uncond']:.3f} ± {r['mc_se_uncond']:.3f} "
            f"(conditional {r['cov_cond']:.3f}, computable {r['comp_rate']:.3f})."
        )
    lines.append("")
    path.write_text("\n".join(lines))
    return verdict


def main():
    print("loading Monday prefix", flush=True)
    frame, feats = load_cicids(cic_dir() / "Monday-WorkingHours.pcap_ISCX.csv")
    missing = [f for f in SERIES if f not in feats]
    if missing:
        raise SystemExit(f"missing columns: {missing}")
    cov_rows, metas = [], []
    for feature in SERIES:
        print(f"series {feature}", flush=True)
        rec = trace_record(frame, feature)
        print(
            f"  n={rec['n_trace']} Geyer {rec['dif_geyer']:.2f} batch {rec['dif_batch']:.2f} L={rec['L']}",
            flush=True,
        )
        rows, meta = run_series(rec)
        cov_rows.extend(rows)
        metas.append(meta)
    out = ROOT / "results"
    cov = pd.DataFrame(cov_rows)
    meta = pd.DataFrame(metas)
    cov.to_csv(out / "trace_coverage.csv", index=False)
    meta.to_csv(out / "trace_coverage_meta.csv", index=False)
    verdict = write_gate(ROOT / "docs" / "week2_gate.md", cov, meta)
    print(verdict, flush=True)


if __name__ == "__main__":
    main()
