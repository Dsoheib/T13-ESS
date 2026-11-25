"""Conceptual figure: the full evaluation pipeline, from a time-ordered test set to the
reporting line, with the two evidence sources that score it. No data is read; every label
restates a definition from the Materials and Methods section.
"""
import os
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

_PDFMETA = {"CreationDate": None}
os.makedirs("paper/figures", exist_ok=True)
CM = 1 / 2.54

INPUT = "#eef2f7"
SERIES = "#dce6f2"
EST = "#f2f2f2"
GATE = "#fdf1d6"
AWARE = "#4f81bd"
STOP = "#c0504d"
VALID = "#e8f0e0"
EDGE = "0.35"
FS, FS_SMALL, FS_HEAD = 6.0, 5.6, 6.8


def box(ax, x, y, w, h, text, fc, ec=EDGE, fs=FS, weight="normal", color="black", lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2",
                                fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight=weight, color=color, zorder=3, linespacing=1.25)


def arrow(ax, p, q, color=EDGE, style="-|>", ls="-", text=None, toff=(0, 1.4)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, lw=0.8,
                                 color=color, ls=ls, zorder=1, shrinkA=1, shrinkB=1))
    if text:
        ax.text((p[0] + q[0]) / 2 + toff[0], (p[1] + q[1]) / 2 + toff[1], text,
                ha="center", va="center", fontsize=FS_SMALL, color=color, style="italic")


fig = plt.figure(figsize=(17.4 * CM, 9.4 * CM), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 174)
ax.set_ylim(0, 94)
ax.axis("off")

# Stage headers.
for x, label in ((14, "1  Test set"), (47, "2  Metric series"),
                 (82, "3  Dependence"), (109, "4  Gate"),
                 (139, "5  Interval"), (165, "6  Report")):
    ax.text(x, 90, label, fontsize=FS_HEAD, fontweight="bold", color="#1f3b5c", va="center",
            ha="center")

# 1. Input.
box(ax, 2, 48, 24, 36,
    "Time-ordered\ntest sequence\n\nscores $s_t$, labels $y_t$\n\nthreshold frozen\nfrom training split",
    INPUT)

# 2. Per-metric series.
rows = {"fpr": 72, "rec": 58, "auc": 44}
box(ax, 31, rows["fpr"], 32, 10, "FPR: benign alarm indicator\n$I(s_t>\\mathrm{thr})$, $y_t{=}0$", SERIES)
box(ax, 31, rows["rec"], 32, 10, "Recall: attack-row\nindicators, in attack order", SERIES)
box(ax, 31, rows["auc"], 32, 10, "AUC: joint $(y_t,s_t)$ series\n(sets the block length $L$)", SERIES)
for r in rows.values():
    arrow(ax, (26.6, 66), (30.6, r + 5))

# 3. Dependence estimate.
box(ax, 70, 50, 24, 30,
    "$\\hat\\tau_{\\mathrm{int}}$ by Geyer\n(primary) and\nbatch means\n(robustness)\n\n"
    "$n_{\\mathrm{eff}}=n/\\hat\\tau_{\\mathrm{int}}$\n$\\mathrm{DIF}=n/n_{\\mathrm{eff}}$",
    EST)
for r in rows.values():
    arrow(ax, (63.6, r + 5), (69.6, 65))

# 4. Gate.
box(ax, 99, 52, 20, 26,
    "Estimators agree\nwithin $2\\times$ on the\nbenign score\nseries, and\n$n_{\\mathrm{eff}}\\geq 50$?",
    GATE, ec="#b38600")
arrow(ax, (94.6, 65), (98.6, 65))

# 5. Intervals (yes branch) and the stop (no branch).
box(ax, 124, 72, 30, 10, "ESS-adjusted Wilson\n($n$ replaced by $n_{\\mathrm{eff}}$)",
    "white", ec=AWARE, lw=1.0)
box(ax, 124, 58, 30, 10, "ESS normal plug-in on\nthe attack subsequence", "white", ec=AWARE, lw=1.0)
box(ax, 124, 44, 30, 10, "Moving-block bootstrap of\nMann\u2013Whitney on $(y_t,s_t)$",
    "white", ec=AWARE, lw=1.0)
for r in rows.values():
    arrow(ax, (119.6, 68 if r > 60 else 62), (123.6, r + 5), color=AWARE)
ax.text(121.5, 80.5, "yes", fontsize=FS_SMALL, color=AWARE, style="italic", ha="center")
box(ax, 124, 30, 30, 9, "Report $n_{\\mathrm{eff}}$ only;\nno interval", "#f9e3e2", ec=STOP, lw=1.0)
arrow(ax, (109, 51.6), (123.6, 34.5), color=STOP)
ax.text(112.5, 40.5, "no", fontsize=FS_SMALL, color=STOP, style="italic", ha="center")

# 6. Reporting line.
box(ax, 158, 34, 14, 48,
    "Reporting\nline\n\nmetric\nprocedure\n$n_{\\mathrm{eff}}$\nestimated\nDIF\nagreement\nflag\n"
    "block\nlength $L$", INPUT, fs=FS_SMALL)
for y in (77, 63, 49, 34.5):
    arrow(ax, (154.6, y), (157.6, y if y > 40 else 40))

# Evidence band: what scores the pipeline.
ax.add_patch(FancyBboxPatch((2, 2), 170, 22, boxstyle="round,pad=0.25,rounding_size=1.5",
                            fc="none", ec="0.6", lw=0.6, ls=(0, (3, 2)), zorder=0))
ax.text(4, 21, "Evidence that scores the pipeline", fontsize=FS_HEAD, fontweight="bold",
        color="#3d5a1f", va="center")
box(ax, 4, 4, 52, 13.5,
    "Coverage simulation (§4.1–4.3)\nAR(1) or fGn background × Markov campaigns;\n"
    "Hurst grid; $n=5000$ and $20000$", VALID, fs=FS_SMALL)
box(ax, 61, 4, 52, 13.5,
    "Telemetry (§4.4, §4.8)\nCICIDS2017 and AAL, time-order audited;\n"
    "packet, flow and window grain", VALID, fs=FS_SMALL)
box(ax, 118, 4, 52, 13.5,
    "Paired AUC difference (§4.7)\nthe estimand a ranking rests on;\n"
    "no usable interval under campaigns", "#f9e3e2", ec=STOP, fs=FS_SMALL)
arrow(ax, (58.5, 10), (58.5, 29.5), ls=(0, (2, 1.5)))
ax.text(60, 27, "coverage against a named target", fontsize=FS_SMALL, style="italic",
        color=EDGE, va="center")

fig.savefig("paper/figures/fig_pipeline.pdf", metadata=_PDFMETA)
fig.savefig("paper/figures/fig_pipeline.png", dpi=300)
plt.close()
