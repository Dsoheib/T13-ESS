"""Two manuscript figures. Every bar and interval is read from a results CSV.

fig_coverage: nominal-n versus the dependence-aware interval, with the H=0.8 cell.
fig_decision: Monday beside Wednesday false-positive intervals, and the three
Wednesday detector pairs (i.i.d. basic versus moving-block basic).
"""
import os
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import pandas as pd
# Deterministic output: matplotlib stamps a CreationDate into the PDF, which would make
# `make all` dirty the tree on every run. Pinning it keeps the build idempotent.
_PDFMETA = {"CreationDate": None}

os.makedirs("paper/figures", exist_ok=True)
CM = 1 / 2.54
NAIVE = "#c0504d"
AWARE = "#4f81bd"
NOMINAL = 0.95

cov = pd.read_csv("results/coverage_sim.csv")
cov20 = pd.read_csv("results/coverage_sim_n20000.csv")

def cell(frame, scenario, metric, interval):
    r = frame[(frame.scenario == scenario) & (frame.metric == metric) & (frame.interval == interval)]
    if len(r) != 1:
        raise SystemExit(f"figure: expected one coverage row for {scenario}/{metric}/{interval}")
    r = r.iloc[0]
    return float(r.cov_uncond), float(r.mc_se_uncond)

# Dependence-aware procedure that carries the claim for each metric.
AWARE_IV = {"fpr": "corrWilson", "recall": "ess", "auc": "mbb"}
NAIVE_IV = {"fpr": "naiveWilson", "recall": "naiveNormal", "auc": "naiveBoot"}
METRICS = [("fpr", "FPR"), ("recall", "Recall"), ("auc", "AUC")]

def panel(ax, frame, scenario, title):
    import numpy as np
    x = np.arange(len(METRICS))
    w = 0.36
    for shift, ivmap, color, label in (
        (-w / 2, NAIVE_IV, NAIVE, "nominal $n$"),
        (w / 2, AWARE_IV, AWARE, "dependence-aware"),
    ):
        vals, errs = [], []
        for metric, _ in METRICS:
            v, e = cell(frame, scenario, metric, ivmap[metric])
            vals.append(v)
            errs.append(e)
        ax.bar(x + shift, vals, width=w, color=color, label=label, zorder=2)
        ax.errorbar(x + shift, vals, yerr=errs, fmt="none", ecolor="black",
                    elinewidth=0.6, capsize=2, zorder=3)
    ax.axhline(NOMINAL, color="0.25", lw=0.7, ls="--", zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, lab in METRICS])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("unconditional coverage")
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig, axes = plt.subplots(1, 2, figsize=(16 * CM, 7.2 * CM), dpi=300, sharey=True)
panel(axes[0], cov20, "bg_ar__lab_campaign", "Short memory, $n=20000$")
panel(axes[1], cov, "lrd_H0.8", "Long memory $H=0.8$, $n=5000$")
axes[1].set_ylabel("")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=8,
           bbox_to_anchor=(0.5, -0.02))
fig.tight_layout()
fig.savefig("paper/figures/fig_coverage.pdf", bbox_inches="tight", metadata=_PDFMETA)
fig.savefig("paper/figures/fig_coverage.png", bbox_inches="tight")
plt.close()

ml = pd.read_csv("results/metric_level_intervals.csv")
pairs = pd.read_csv("results/paired_block_comparisons.csv")

def fpr_row(dataset, detector):
    r = ml[(ml.dataset == dataset) & (ml.detector == detector) & (ml.metric == "fpr")]
    if len(r) != 1:
        raise SystemExit(f"figure: expected one FPR row for {dataset}/{detector}")
    return r.iloc[0]

fpr_rows = [
    ("Mon, IF", fpr_row("CICIDS2017-Mon", "iforest")),
    ("Wed, IF", fpr_row("CICIDS2017-Wed", "iforest")),
    ("Wed, LR", fpr_row("CICIDS2017-Wed", "logreg")),
    ("Wed, RF", fpr_row("CICIDS2017-Wed", "rf")),
]
wed_pairs = ["iforest-logreg", "iforest-rf", "logreg-rf"]
pair_rows = []
for name in wed_pairs:
    r = pairs[(pairs.dataset == "CICIDS2017-Wed") & (pairs.pair == name) & (pairs.statistic == "auc_diff")]
    if len(r) != 1:
        raise SystemExit(f"figure: expected one Wednesday AUC pair {name}")
    pair_rows.append(r.iloc[0])
if not bool(pair_rows[-1].flip_iid_sig_mbb_not):
    raise SystemExit("figure: Wednesday logreg-rf is no longer the i.i.d.-only flip; redraw the caption")

fig, (ax_f, ax_a) = plt.subplots(1, 2, figsize=(16 * CM, 7.6 * CM), dpi=300)
for i, (lab, r) in enumerate(fpr_rows):
    y = len(fpr_rows) - 1 - i
    ax_f.plot([r.naive_lo, r.naive_hi], [y + 0.12, y + 0.12], color=NAIVE, lw=1.6, solid_capstyle="butt")
    ax_f.plot([r.corr_lo, r.corr_hi], [y - 0.12, y - 0.12], color=AWARE, lw=1.6, solid_capstyle="butt")
    ax_f.plot(r.estimate, y, "o", color="0.15", ms=3, zorder=3)
ax_f.set_yticks(range(len(fpr_rows)))
ax_f.set_yticklabels([lab for lab, _ in fpr_rows][::-1])
ax_f.set_xlabel("false-positive rate")
ax_f.set_title("Alarm indicator", fontsize=9)
ax_f.tick_params(labelsize=8)
ax_f.spines["top"].set_visible(False)
ax_f.spines["right"].set_visible(False)

labels_r = []
for i, r in enumerate(pair_rows):
    y = len(pair_rows) - 1 - i
    ax_a.plot([r.iid_lo, r.iid_hi], [y + 0.12, y + 0.12], color=NAIVE, lw=1.6, solid_capstyle="butt")
    ax_a.plot([r.mbb_lo, r.mbb_hi], [y - 0.12, y - 0.12], color=AWARE, lw=1.6, solid_capstyle="butt")
    ax_a.plot(r.estimate, y, "o", color="0.15", ms=3, zorder=3)
    mark = r.pair.replace("iforest", "IF").replace("logreg", "LR").replace("rf", "RF")
    if r.series_status != "qualifying":
        mark += "*"
    labels_r.append(mark)
ax_a.axvline(0, color="0.25", lw=0.7, ls="--", zorder=0)
hi = max(max(r.iid_hi, r.mbb_hi) for r in pair_rows)
lo = min(min(r.iid_lo, r.mbb_lo) for r in pair_rows)
pad = 0.04 * (hi - lo)
ax_a.set_xlim(lo - pad, hi + pad)
ax_a.set_yticks(range(len(pair_rows)))
ax_a.set_yticklabels(labels_r[::-1])
ax_a.set_xlabel("AUC difference")
ax_a.set_title("Wednesday detector pairs", fontsize=9)
ax_a.tick_params(labelsize=8)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)
flip = pair_rows[-1]
ax_a.annotate("block interval includes 0", xy=(float(flip.mbb_hi), -0.12),
              xytext=(-0.16, 0.85), fontsize=7, color="0.15",
              arrowprops=dict(arrowstyle="->", color="0.35", lw=0.6))
from matplotlib.lines import Line2D

leg = [Line2D([0], [0], color=NAIVE, lw=1.6), Line2D([0], [0], color=AWARE, lw=1.6)]
ax_f.legend(leg, ["nominal $n$", "ESS--Wilson"], frameon=False, fontsize=7, loc="upper right")
ax_a.legend(leg, ["i.i.d.", "moving block"], frameon=False, fontsize=7, loc="upper center")
fig.tight_layout()
fig.savefig("paper/figures/fig_decision.pdf", bbox_inches="tight", metadata=_PDFMETA)
fig.savefig("paper/figures/fig_decision.png", bbox_inches="tight")
plt.close()
print("wrote fig_coverage and fig_decision")
