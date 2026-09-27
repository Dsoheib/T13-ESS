"""Graphical abstract: FPR coverage by the order the interval is allowed to see,
plus the autocorrelation time in that order.
Numbers come from results/split_order_arms.csv and results/split_order_arms_meta.csv.
None is hand-typed.
Primary output: paper/figures/graphical_abstract.pdf (vector, embedded fonts, 13 x 5.2 cm,
Elsevier-preferred). A PNG is also written for preview only.
Run by `make all`.
"""
import os
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42   # embed TrueType, not Type 3
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

# Deterministic output: matplotlib stamps a CreationDate into the PDF, which would make
# `make all` dirty the tree on every run. Pinning it keeps the build idempotent.
_PDFMETA = {"CreationDate": None}

os.makedirs("paper/figures", exist_ok=True)
arms = pd.read_csv("results/split_order_arms.csv")
meta = pd.read_csv("results/split_order_arms_meta.csv").iloc[0]

def fpr(arm, iv):
    r = arms[(arms.arm == arm) & (arms.interval == iv)]
    return float(r.cov_uncond.iloc[0])

order = [
    ("temporal", "time-ordered", float(meta.tau_temporal_seen)),
    ("shuffled", "shuffled", float(meta.tau_shuffled_seen)),
    ("restored", "time restored", float(meta.tau_shuffled_true)),
]
NOMINAL = 0.95

CM = 1 / 2.54
fig = plt.figure(figsize=(13 * CM, 5.2 * CM), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.45,
                      left=0.09, right=0.985, top=0.78, bottom=0.28)
TS, LS, VS, NS = 6.5, 6.0, 5.5, 5.0  # title, label, value, note sizes
colors = {"naiveWilson": "#c0504d", "essWilson": "#4f81bd"}

# ---- left: coverage by the order the interval sees ----
axL = fig.add_subplot(gs[0, 0])
width = 0.36
for j, (arm, lab, _) in enumerate(order):
    for k, iv in enumerate(("naiveWilson", "essWilson")):
        val = fpr(arm, iv)
        xpos = j + (k - 0.5) * width
        axL.bar(xpos, val, width=width, color=colors[iv],
                label=("naive Wilson" if iv == "naiveWilson" else "ESS-Wilson") if j == 0 else None,
                edgecolor="black", linewidth=0.4)
        axL.text(xpos, val + 0.02, f"{val:.2f}", ha="center", va="bottom", fontsize=VS)
axL.axhline(NOMINAL, ls="--", color="black", lw=0.8)
axL.set_xticks(range(len(order)))
axL.set_xticklabels([lab for _, lab, _ in order], fontsize=LS)
axL.set_xlim(-0.55, 2.55)
axL.set_ylim(0, 1.18)
axL.set_ylabel("FPR interval coverage", fontsize=LS)
axL.set_title("ESS-Wilson recovers when the\ntest order is restored",
              fontsize=TS, fontweight="bold")
handles, labels = axL.get_legend_handles_labels()
handles.append(Line2D([0], [0], color="black", ls="--", lw=0.8))
labels.append("nominal 0.95")
axL.legend(handles, labels, loc="upper center", fontsize=NS, frameon=False, ncol=3,
           bbox_to_anchor=(0.5, -0.22))
axL.tick_params(labelsize=NS)
axL.spines[["top", "right"]].set_visible(False)

# ---- right: autocorrelation time in the order the interval used ----
axR = fig.add_subplot(gs[0, 1])
taus = [t for _, _, t in order]
axR.bar(range(len(taus)), taus, color="#7f7f7f", edgecolor="black", linewidth=0.4, width=0.6)
for i, t in enumerate(taus):
    axR.text(i, t + 0.4, f"{t:.1f}", ha="center", va="bottom", fontsize=VS)
axR.set_xticks(range(len(order)))
axR.set_xticklabels([lab for _, lab, _ in order], fontsize=LS)
axR.set_ylabel(r"$\tau$ in that order", fontsize=LS)
axR.set_ylim(0, max(taus) * 1.25)
axR.set_title("Dependence the interval\ncan see", fontsize=TS, fontweight="bold")
axR.tick_params(labelsize=NS)
axR.spines[["top", "right"]].set_visible(False)

pdf = "paper/figures/graphical_abstract.pdf"
png = "paper/figures/graphical_abstract.png"
fig.savefig(pdf, metadata=_PDFMETA)
fig.savefig(png, dpi=300)
print(f"wrote {pdf} (vector, 13x5.2 cm) and {png} (preview) from results/split_order_arms.csv")
