"""Conceptual figure, vertical layout for single-column journals whose lettering must be at least
9 pt at final size (GUJS). Same content as pipeline_figure.py; the section numbers in the evidence
band are passed on the command line because they differ between versions of the manuscript.

    python3 scripts/pipeline_figure_vertical.py --sim 3.1-3.3 --telemetry "3.4, 3.8" --paired 3.7
"""
import argparse
import os
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ap = argparse.ArgumentParser()
ap.add_argument("--sim", default="4.1–4.3")
ap.add_argument("--telemetry", default="4.4, §4.8")
ap.add_argument("--paired", default="4.7")
ap.add_argument("--out", default="paper/figures/fig_pipeline_vertical")
args = ap.parse_args()
args.sim = args.sim.replace("-", "–")
args.telemetry = args.telemetry.replace(", ", ", §")

_PDFMETA = {"CreationDate": None}
os.makedirs(os.path.dirname(args.out), exist_ok=True)
MM = 1 / 25.4

INPUT, SERIES, EST, GATE = "#eef2f7", "#dce6f2", "#f2f2f2", "#fdf1d6"
AWARE, STOP, VALID, EDGE = "#4f81bd", "#c0504d", "#e8f0e0", "0.35"
FS, FS_HEAD = 9.0, 9.5          # every inscription is at least 9 pt at final size

W, H = 165, 160                 # millimetres; drawn at final size
fig = plt.figure(figsize=(W * MM, H * MM), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")


def box(x, y, w, h, text, fc, ec=EDGE, lw=0.8, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=FS, zorder=3,
            linespacing=1.3, fontweight=weight)


def arrow(p, q, color=EDGE, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, lw=0.9, color=color,
                                 ls=ls, zorder=1, shrinkA=0, shrinkB=0))


def head(x, y, text, color="#1f3b5c"):
    ax.text(x, y, text, fontsize=FS_HEAD, fontweight="bold", color=color, va="bottom")


G = 25                                   # left column for the stage labels
COLS = [(G, 43.5), (G + 46.5, 43.5), (G + 93, 43.5)]   # three metric lanes; x = 163 is the return lane


def stage(y_mid, num, name):
    ax.text(0, y_mid + 1.6, num, fontsize=FS_HEAD + 2, fontweight="bold", color="#1f3b5c",
            va="bottom", ha="left")
    ax.text(0, y_mid + 1.0, name, fontsize=FS, fontweight="bold", color="#1f3b5c", va="top",
            ha="left", linespacing=1.2)


# 1. Test set
stage(147, "1", "Test set")
box(G, 140, 165 - G, 13, "Time-ordered test sequence: scores $s_t$, labels $y_t$;\n"
    "threshold frozen from the training split", INPUT)

# 2. Series each metric uses
stage(122, "2", "Metric\nseries")
series = ["False-positive rate:\nbenign alarm indicator\n$I(s_t>\\mathrm{thr})$, $y_t=0$",
          "Recall:\nattack-row indicators,\nin attack order",
          "AUC:\njoint $(y_t, s_t)$ series\n(sets block length $L$)"]
for (x, w), t in zip(COLS, series):
    arrow((x + w / 2, 140), (x + w / 2, 131.5))
    box(x, 112, w, 19, t, SERIES)

# 3. Dependence estimate, 4. Gate, and the "no" branch
stage(91, "3\u20134", "Dependence\nand gate")
box(G, 80, 42, 22, "$\\hat\\tau_{\\mathrm{int}}$: Geyer\n(primary) and\nbatch means;\n"
    "$n_{\\mathrm{eff}}=n/\\hat\\tau_{\\mathrm{int}}$", EST)
box(G + 46, 80, 49, 22, "Estimators agree\nwithin $2\\times$ on the\nbenign score series,\n"
    "and $n_{\\mathrm{eff}}\\geq 50$?", GATE, ec="#b38600")
box(G + 100, 80, 40, 22, "No: report\n$n_{\\mathrm{eff}}$ only,\nno interval", "#f9e3e2", ec=STOP, lw=1.1)
for (x, w), tx in zip(COLS, (G + 11, G + 21, G + 31)):
    arrow((x + w / 2, 112), (tx, 102.5))
arrow((G + 42, 91), (G + 45.5, 91))
arrow((G + 95, 91), (G + 99.5, 91), color=STOP)
ax.text(G + 97.3, 92.6, "no", fontsize=FS, color=STOP, style="italic", ha="center", va="bottom")

# 5. Metric-specific interval (gate passed)
stage(59, "5", "Interval")
ax.text(G + 73, 75.8, "yes", fontsize=FS, color=AWARE, style="italic", va="center")
intervals = ["ESS-adjusted\nWilson ($n$ replaced\nby $n_{\\mathrm{eff}}$)",
             "ESS normal\nplug-in on the\nattack subsequence",
             "Moving-block\nbootstrap of Mann\u2013\nWhitney on $(y_t, s_t)$"]
for (x, w), t in zip(COLS, intervals):
    arrow((G + 70.5, 80), (x + w / 2, 68.5), color=AWARE)
    box(x, 50, w, 18.5, t, "white", ec=AWARE, lw=1.1)

# 6. Reporting line
stage(33, "6", "Report")
box(G, 27, 165 - G, 13, "Reporting line: metric, procedure, $n_{\\mathrm{eff}}$, estimated DIF,\n"
    "agreement flag, block length $L$", INPUT)
for x, w in COLS:
    arrow((x + w / 2, 50), (x + w / 2, 40.5))
arrow((163, 80), (163, 40.5), color=STOP)

# Evidence that scores the pipeline
ax.add_patch(FancyBboxPatch((0, 0.6), 165, 19.5, boxstyle="round,pad=0,rounding_size=1.6",
                            fc="none", ec="0.55", lw=0.7, ls=(0, (3, 2)), zorder=0))
ev = [(f"Coverage simulation (§{args.sim})\nAR(1)/fGn background × Markov\ncampaigns; Hurst grid",
       VALID, EDGE),
      (f"Telemetry (§{args.telemetry})\nCICIDS2017 and AAL,\ntime-order audited", VALID, EDGE),
      (f"Paired AUC difference (§{args.paired})\nno usable interval\nunder campaigns", "#f9e3e2", STOP)]
for (x, w), (t, fc, ec) in zip([(2, 52), (56.5, 52), (111, 52)], ev):
    box(x, 2.3, w, 16, t, fc, ec=ec)
ax.text(0, 20.8, "Evidence that scores the pipeline", fontsize=FS_HEAD, fontweight="bold",
        color="#3d5a1f", va="bottom")

fig.savefig(args.out + ".pdf", metadata=_PDFMETA)
fig.savefig(args.out + ".png", dpi=300)
plt.close()
