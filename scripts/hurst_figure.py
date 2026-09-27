"""The long-memory boundary, and whether the reporting gate sees it.

Left: unconditional coverage against the Hurst exponent for the three false-positive
constructions, from results/hurst_sweep.csv.
Right: the fraction of replicates the prespecified gate admits, computed on the alarm indicator
and on the benign score series, against the same coverage curve, from diagnostics/p127_gate.csv.

Every point is read from a CSV. No value is typed here.
"""
import os
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Deterministic output, as in week4_figures.py: keep `make all` idempotent.
_PDFMETA = {"CreationDate": None}

os.makedirs("paper/figures", exist_ok=True)
CM = 1 / 2.54
NOMINAL = 0.95
NAIVE = "#c0504d"
AWARE = "#4f81bd"
BLOCK = "#9bbb59"
MASKED = "#8064a2"

hs = pd.read_csv("results/hurst_sweep.csv")
gt = pd.read_csv("diagnostics/p127_gate.csv")
H = np.array(sorted(hs.H.round(2).unique()))


def series(metric, interval, col="cov_uncond"):
    out = []
    for h in H:
        r = hs[(hs.H.round(2) == h) & (hs.metric == metric) & (hs.interval == interval)]
        if len(r) != 1:
            raise SystemExit(f"fig_hurst: expected one row for H={h} {metric}/{interval}")
        out.append(float(r.iloc[0][col]))
    return np.array(out)


def gate(which, col="gate_pass_rate"):
    out = []
    for h in H:
        r = gt[(gt.H.round(2) == h) & (gt.series == which)]
        if len(r) != 1:
            raise SystemExit(f"fig_hurst: expected one p127 row for H={h}/{which}")
        out.append(float(r.iloc[0][col]))
    return np.array(out)


fig, (axl, axr) = plt.subplots(1, 2, figsize=(17.4 * CM, 6.6 * CM))

# ---- left: coverage against H ----
for iv, colour, marker, label in (("naiveWilson", NAIVE, "s", "nominal $n$ (Wilson)"),
                                  ("corrWilson", AWARE, "o", "ESS-Wilson"),
                                  ("mbb", BLOCK, "^", "moving block")):
    y, e = series("fpr", iv), series("fpr", iv, "mc_se_uncond")
    axl.errorbar(H, y, yerr=e, color=colour, marker=marker, ms=4.5, lw=1.4,
                 capsize=2.5, label=label)
axl.axhline(NOMINAL, ls="--", lw=0.9, color="0.35")
axl.text(H[0], NOMINAL + 0.012, "nominal 0.95", fontsize=7, color="0.35")
axl.set_xlabel("Hurst exponent $H$", fontsize=8.5)
axl.set_ylabel("unconditional coverage", fontsize=8.5)
axl.set_title("Coverage degrades monotonically in $H$", fontsize=9)
axl.set_ylim(0.0, 1.03)
axl.legend(fontsize=7, frameon=False, loc="lower left")

# ---- right: does the gate see it? ----
cov = series("fpr", "corrWilson")
axr.plot(H, cov, color=AWARE, marker="o", ms=4.5, lw=1.4, label="ESS-Wilson coverage")
axr.plot(H, gate("alarm"), color=MASKED, marker="D", ms=4.5, lw=1.4, ls=":",
         label="gate admits, alarm indicator")
axr.plot(H, gate("score"), color="0.15", marker="v", ms=4.5, lw=1.4, ls="-.",
         label="gate admits, benign score")
axr.axhline(NOMINAL, ls="--", lw=0.9, color="0.35")
axr.text(H[0], NOMINAL + 0.012, "nominal 0.95", fontsize=7, color="0.35")
axr.set_xlabel("Hurst exponent $H$", fontsize=8.5)
axr.set_ylabel("fraction of replicates", fontsize=8.5)
axr.set_title("The indicator gate admits what the score gate rejects", fontsize=9)
axr.set_ylim(0.0, 1.03)
axr.legend(fontsize=7, frameon=False, loc="lower left")

for ax in (axl, axr):
    ax.tick_params(labelsize=7.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

fig.tight_layout()
fig.savefig("paper/figures/fig_hurst.pdf", bbox_inches="tight", metadata=_PDFMETA)
fig.savefig("paper/figures/fig_hurst.png", bbox_inches="tight", dpi=300)
print("wrote fig_hurst from results/hurst_sweep.csv and diagnostics/p127_gate.csv")
