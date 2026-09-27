"""P99: apply the project's estimator-agreement rule uniformly to every DIF series and emit a
per-series qualifying/flagged/not-estimable classification, then the per-grain HEADLINE = median
over qualifying series (all-series median reported beside it, labelled).

Rule (a series enters a headline only if all three hold):
  (i)  it is not a deterministic function of the index (time encodings / counters / sequence
       numbers are EXCLUDED, reason stated);
  (ii) Geyer and batch-means agree within 2x;
  (iii) n_eff >= 50.
Failing (ii) -> reported as an estimator range [min(geyer,batch), max] with its flag.
Failing (iii) -> reported not estimable.

Inputs: results/dif_by_dataset.csv (AAL window + CICIDS flow, carry geyer+batch),
        results/packet_windows.csv (packet grain, carries geyer+batch+n_eff).
Output: results/dif_headline.csv (per-series) + results/dif_headline_macros.tex (medians).
No number is hand-typed downstream: make_tables + the abstract macros read this file.
"""
import numpy as np, pandas as pd

# deterministic-of-the-clock / index series: measuring their autocorrelation measures the encoding
DETERMINISTIC = {"time_sin", "time_cos", "freq_persistence_5w"}
AGREE_FACTOR = 2.0
NEFF_FLOOR = 50


def classify(geyer, batch, n_conservative, series_base):
    """n_conservative = n / max(geyer, batch): the larger DIF gives the smaller n_eff, used for
    BOTH the >=50 test and the reported value (P108)."""
    if series_base in DETERMINISTIC:
        return "excluded-deterministic", np.nan
    if geyer is None or batch is None or (isinstance(geyer, float) and np.isnan(geyer)):
        return "not-estimable", np.nan
    ratio = max(geyer, batch) / max(min(geyer, batch), 1e-9)
    if n_conservative is not None and not np.isnan(n_conservative) and n_conservative < NEFF_FLOOR:
        return "not-estimable", np.nan          # (iii) fails on the conservative n_eff
    if ratio > AGREE_FACTOR:
        return "estimator-range", np.nan        # (ii) fails
    return "qualifying", float(geyer)


def neff_report(n, geyer, batch, status):
    """Conservative n_eff = n/max(DIF) (P108). Estimator-range series report a range
    [n/max, n/min]. Returns (numeric_conservative, display_string)."""
    if np.isnan(n) or np.isnan(geyer) or np.isnan(batch):
        return np.nan, "--"
    hi_dif, lo_dif = max(geyer, batch), min(geyer, batch)
    cons = n / hi_dif
    if status == "estimator-range":
        return cons, f"{cons:.0f}-{n/lo_dif:.0f}"
    return cons, f"{cons:.0f}"


rows = []

# ---- AAL window grain, from dif_by_dataset.csv (feature rows) ----
g = pd.read_csv("results/dif_by_dataset.csv")
gg = g[(g.family == "feature") & (g.dataset.str.startswith("AAL"))].copy()
for _, r in gg.iterrows():
    base = str(r.series).split("|")[0]
    geyer = pd.to_numeric(r.dif_geyer, errors="coerce")
    batch = pd.to_numeric(r.dif_batch, errors="coerce")
    n = pd.to_numeric(r["n"], errors="coerce")
    n_cons = n / max(geyer, batch) if not (np.isnan(n) or np.isnan(geyer) or np.isnan(batch)) else np.nan
    status, dif_q = classify(geyer, batch, n_cons, base)
    _, neff_disp = neff_report(n, geyer, batch, status)
    rows.append(dict(dataset=r.dataset, grain="window", series=base, n=int(n) if not np.isnan(n) else None,
                     n_eff=round(float(n_cons), 1) if not np.isnan(n_cons) else None, n_eff_disp=neff_disp,
                     geyer=None if np.isnan(geyer) else round(float(geyer), 2),
                     batch=None if np.isnan(batch) else round(float(batch), 2),
                     status=status, dif_qualifying=None if np.isnan(dif_q) else round(dif_q, 2)))

# ---- CICIDS flow grain, from cicids_flow_dif.csv: the (b) within-minute-shuffle cells, all 3 days
#      (P106). Agreement rule applied to (b) with geyer=dif_b_headline, batch=dif_b_batch. ----
cf = pd.read_csv("results/cicids_flow_dif.csv")
for _, r in cf.iterrows():
    geyer = pd.to_numeric(r.dif_b_headline, errors="coerce")   # (b) Geyer
    batch = pd.to_numeric(r.get("dif_b_batch"), errors="coerce")  # (b) batch
    n = pd.to_numeric(r.get("n_b"), errors="coerce")
    n_cons = n / max(geyer, batch) if not (np.isnan(n) or np.isnan(geyer) or np.isnan(batch)) else np.nan
    base = f"{r.feature} ({r.day})"
    status, dif_q = classify(geyer, batch, n_cons, str(r.feature))
    _, neff_disp = neff_report(n, geyer, batch, status)
    rows.append(dict(dataset="CICIDS2017", grain="flow", series=base, n=int(n) if not np.isnan(n) else None,
                     n_eff=round(float(n_cons), 1) if not np.isnan(n_cons) else None, n_eff_disp=neff_disp,
                     geyer=None if np.isnan(geyer) else round(float(geyer), 2),
                     batch=None if np.isnan(batch) else round(float(batch), 2),
                     status=status, dif_qualifying=None if np.isnan(dif_q) else round(dif_q, 2)))

# ---- packet grain, from packet_windows.csv ----
pk = pd.read_csv("results/packet_windows.csv")
for _, r in pk.iterrows():
    geyer = pd.to_numeric(r.dif_geyer, errors="coerce")
    batch = pd.to_numeric(r.dif_batch, errors="coerce")
    n_eff_given = pd.to_numeric(r.n_eff, errors="coerce")     # = n/geyer as shipped
    n = n_eff_given * geyer if not (np.isnan(n_eff_given) or np.isnan(geyer)) else np.nan
    n_cons = n / max(geyer, batch) if not (np.isnan(n) or np.isnan(geyer) or np.isnan(batch)) else np.nan
    base = str(r.series)
    status, dif_q = classify(geyer, batch, n_cons, base)
    _, neff_disp = neff_report(n, geyer, batch, status)
    rows.append(dict(dataset="CICIDS2017-Wed", grain="packet", series=f"{r.series}|{r.window}",
                     n=int(n) if not np.isnan(n) else None,
                     n_eff=round(float(n_cons), 1) if not np.isnan(n_cons) else None, n_eff_disp=neff_disp,
                     geyer=None if np.isnan(geyer) else round(float(geyer), 2),
                     batch=None if np.isnan(batch) else round(float(batch), 2),
                     status=status, dif_qualifying=None if np.isnan(dif_q) else round(dif_q, 2)))

out = pd.DataFrame(rows)
out.to_csv("results/dif_headline.csv", index=False)
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 80)
print(out.to_string(index=False))

# ---- per-grain headline = median over qualifying series ----
macros = []
print("\n=== per-grain headline (median over QUALIFYING series) ===")
for grain in ["packet", "flow", "window"]:
    sub = out[out.grain == grain]
    q = sub[sub.status == "qualifying"]["dif_qualifying"].dropna()
    allser = pd.to_numeric(sub["geyer"], errors="coerce").dropna()
    hq = float(np.median(q)) if len(q) else float("nan")
    ha = float(np.median(allser)) if len(allser) else float("nan")
    print(f"{grain:7s}: qualifying n={len(q)} median={hq:.2f}   |   all-series n={len(allser)} median={ha:.2f}")
    if len(q):
        macros.append((grain, hq, len(q)))

name = {"packet": "PacketQ", "flow": "FlowQ", "window": "WindowQ"}
with open("results/dif_headline_macros.tex", "w") as f:
    for grain, hq, nq in macros:
        f.write(f"\\newcommand{{\\{name[grain]}}}{{{hq:.1f}}}\n")
        f.write(f"\\newcommand{{\\{name[grain]}n}}{{{nq}}}\n")
print("\nwrote results/dif_headline.csv + results/dif_headline_macros.tex")
