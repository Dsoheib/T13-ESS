"""Generate every numeric table in the manuscript from results/ + corpus/ + diagnostics/.
No number in the paper is hand-typed. Run by `make all`. Outputs to paper/tables/*.tex.
"""
import os, sys, pandas as pd, numpy as np
OUT = "paper/tables"; os.makedirs(OUT, exist_ok=True)
def w(name, latex):
    open(os.path.join(OUT, name), "w").write(latex); print("wrote", name)

# ---- T1: coverage by procedure. Not one "corrected" column.
# Cell = unconditional coverage ± MC SE. Where the interval is not always computable,
# append (conditional coverage, computable fraction). Numbers are read from the CSV.
d = pd.read_csv("results/coverage_sim.csv")
d20 = pd.read_csv("results/coverage_sim_n20000.csv")
# heavy_tail stays in the CSV and is not a coverage row: it was scored against the
# Gaussian conditional formula, not the Student-t tail.
scn_lbl = [("bg_iid__lab_scatter","iid (control)"),("bg_iid__lab_campaign","campaigns only"),
           ("bg_ar__lab_scatter","background only"),("bg_ar__lab_campaign","both"),
           ("lrd_H0.8","long-range ($H{=}0.8$)")]

def cell(df, scn, metric, interval):
    r = df[(df.scenario==scn)&(df.metric==metric)&(df.interval==interval)]
    if len(r) == 0 or pd.isna(r.cov_uncond.iloc[0]):
        return "--"
    u = float(r.cov_uncond.iloc[0]); su = float(r.mc_se_uncond.iloc[0])
    comp = float(r.comp_rate.iloc[0])
    top = f"${u:.2f}\\pm{su:.2f}$"
    if comp < 0.995 and not pd.isna(r.cov_cond.iloc[0]):
        sc = float(r.mc_se_cond.iloc[0])
        bot = f"$({float(r.cov_cond.iloc[0]):.2f}\\pm{sc:.2f},\\,{comp:.2f})$"
        return f"\\cellbr{{{top}}}{{{bot}}}"
    return top

def star(spec, body):
    return ("\\begin{tabular*}{\\tabwidth}{@{\\extracolsep{\\fill}}"
            + spec + "@{}}\n" + body + "\\end{tabular*}\n")

def metric_table(df, intervals, colheads, scenarios):
    head = " & ".join(colheads)
    rows = []
    for s, lab in scenarios:
        vals = " & ".join(cell(df, s, m, iv) for m, iv in intervals)
        rows.append(f"{lab} & {vals} \\\\")
    return star("l" + "c"*len(intervals),
                "\\toprule\n" + f"scenario & {head}\\\\\n\\midrule\n"
                + "\n".join(rows) + "\n\\bottomrule\n")

NOTE = ("%\n% cell = unconditional coverage $\\pm$ Monte Carlo SE;"
        " parenthesis = (conditional coverage $\\pm$ its Monte Carlo SE, computable fraction)"
        " when that fraction is below 0.995\n")
w("tab_coverage_fpr.tex", NOTE + metric_table(d, [
    ("fpr","naiveWilson"), ("fpr","corrWilson"), ("fpr","mbb")],
    ["naive Wilson", "ESS-Wilson", "\\cellbr{moving}{block}"], scn_lbl))
w("tab_coverage_recall.tex", NOTE + metric_table(d, [
    ("recall","naiveNormal"), ("recall","ess"), ("recall","episode"), ("recall","mbb")],
    ["\\cellbr{naive}{normal}", "\\cellbr{ESS}{plug-in}",
     "\\cellbr{episode}{bootstrap}", "\\cellbr{moving}{block}"], scn_lbl))
w("tab_coverage_auc.tex", NOTE + metric_table(d, [
    ("auc","naiveBoot"), ("auc","mbb"), ("auc","bjk")],
    ["\\cellbr{i.i.d.}{bootstrap}", "\\cellbr{moving}{block}",
     "\\cellbr{block}{jackknife}"], scn_lbl))
# n=20000 confirmation has no episode bootstrap and no long-range/heavy-tail rows
scn20 = [x for x in scn_lbl if x[0] in set(d20.scenario)]
w("tab_coverage_n20000.tex", NOTE + metric_table(d20, [
    ("fpr","naiveWilson"), ("fpr","corrWilson"),
    ("recall","naiveNormal"), ("recall","ess"),
    ("auc","naiveBoot"), ("auc","mbb")],
    ["\\cellbr{FPR}{naive}", "\\cellbr{FPR}{ESS-Wilson}",
     "\\cellbr{recall}{naive}", "\\cellbr{recall}{ESS}",
     "\\cellbr{AUC}{i.i.d.}", "\\cellbr{AUC}{block}"], scn20))
# legacy filename kept as the FPR table so older links do not point at a mixed column
w("tab_coverage.tex", open(os.path.join(OUT, "tab_coverage_fpr.tex")).read())

# ---- T2: CICIDS flow-grain DIF, (b) headline with (a) as-shipped shown alongside, per feature x day ----
f = pd.read_csv("results/cicids_flow_dif.csv")
piv_b = f.pivot(index="feature", columns="day", values="dif_b_headline")
piv_a = f.pivot(index="feature", columns="day", values="dif_a_asshipped")
days=["Mon","Tue","Wed"]
rows=[]
for feat in piv_b.index:
    cells=" & ".join(f"{piv_b.loc[feat,dd]:.1f} ({piv_a.loc[feat,dd]:.0f})" for dd in days)
    rows.append(f"{feat} & {cells} \\\\")
w("tab_flow_dif.tex", star(">{\\raggedright\\arraybackslash}p{2.35cm}ccc",
  "\\toprule\nbenign feature & Mon & Tue & Wed\\\\\n\\midrule\n"
  + "\n".join(rows) + "\n\\bottomrule\n"))

# ---- T3: three-grain DIF summary under the estimator-agreement rule (P99) ----
# Headline = median over QUALIFYING series (non-deterministic, Geyer/batch within 2x, n_eff>=50);
# the all-series median is shown beside it, labelled. Driven by results/dif_headline.csv.
dh = pd.read_csv("results/dif_headline.csv")
def grain_cells(grain):
    s = dh[dh.grain == grain]
    q = s[s.status == "qualifying"]
    med_q = pd.to_numeric(q.dif_qualifying, errors="coerce").dropna()
    med_all = pd.to_numeric(s.geyer, errors="coerce").dropna()
    nq, ner, nne, nex = (s.status == "qualifying").sum(), (s.status == "estimator-range").sum(), \
        (s.status == "not-estimable").sum(), (s.status == "excluded-deterministic").sum()
    hq = f"{med_q.median():.1f}" if len(med_q) else "--"
    ha = f"{med_all.median():.0f}" if len(med_all) else "--"
    return hq, int(nq), ha, int(ner), int(nne), int(nex)
rows = []
lbl = {"packet": "packet (CICIDS pcap)", "flow": "flow (CICIDS as-shipped)", "window": "window (AAL, owned)"}
for grain in ["packet", "flow", "window"]:
    hq, nq, ha, ner, nne, nex = grain_cells(grain)
    flags = f"{ner} range, {nne} not-est."
    if nex:
        flags += f", {nex} determ."
    rows.append(f"{lbl[grain]} & {hq} ({nq}) & {ha} & {flags} \\\\")
w("tab_grain_summary.tex", star(
  ">{\\raggedright\\arraybackslash}p{2.2cm}cc>{\\raggedright\\arraybackslash}p{2.15cm}",
  "\\toprule\n grain (dataset) & \\cellbr{qualifying}{DIF ($n$)} & \\cellbr{all-series}{median} & other series\\\\\n\\midrule\n"
  + "\n".join(rows) + "\n\\bottomrule\n")
  + "% The qualifying entry is the median of the qualifying series. n=1 is that single series, not a distributional median.\n"
  + "% flow qualifying is the as-shipped (a) order; the within-minute-shuffle (b) median is 17, Table~\\ref{tab:flowdif}\n")

# ---- T4: SF-1 conflation gap, read from the diagnostic run (diagnostics/p1_estimand.py) ----
_p1 = pd.read_csv("diagnostics/p1_iid.csv")
def _p1cov(interval, estimand):
    r = _p1[(_p1.metric == "fpr") & (_p1.interval == interval) & (_p1.estimand == estimand)]
    if len(r) != 1:
        raise SystemExit(f"tab_sf1: expected one p1_iid row for fpr/{interval}/{estimand}")
    return f"{float(r.coverage.iloc[0]):.2f}"
_p1R = int(_p1.R_used.max())
w("tab_sf1.tex", star("llc",
  "\\toprule\ninterval & estimand & coverage\\\\\n\\midrule\n"
  f"naive-normal FPR & population (deployment) & {_p1cov('naive','pop')}\\\\\n"
  f"naive-normal FPR & threshold-conditional & {_p1cov('naive','cond')}\\\\\n"
  f"Wilson FPR & threshold-conditional & {_p1cov('wilson','cond')}\\\\\n"
  "\\bottomrule\n")
  + f"% source: diagnostics/p1_estimand.py -> diagnostics/p1_iid.csv, iid, R={_p1R}\n")

# ---- T5: SF-2 distribution, two cuts + unknown (P71/C3) ----
# NOTE on denominators (P123). Two distinct populations are reported in the paper and they must
# never share the word "resolved" unqualified:
#   * the IN-FRAME SCREENING POOL (corpus/screening_results.csv + inclusion_log.csv) -- the frame
#     of the retired H1, i.e. records using a time-aware split AND reporting uncertainty. Its
#     macros are \Ninframe / \NinframeRes / \ResRate, written with the corpus macros below.
#   * the SF-2 CODING SET (this file) -- every screened record coded for which estimand its
#     reported uncertainty targets, whether or not its split was time-aware. Its macros are
#     \NsfTwo / \NsfTwoRes / \NsfTwoStrict / \NsfTwoUnres, written here.
# SF-2 does not require a time-aware split, so its denominator is the larger one.
s = pd.read_csv("corpus/sf2_uncertainty_kind.csv")
res = s[s.status=="resolved"]; strict = res[res.source.str.startswith(("fulltext","arxiv"))]
unk = int((s.status=="unknown").sum())
def kc(df,k): return int((df.uncertainty_kind==k).sum())
SFTWO_MACROS = (
  f"\\newcommand{{\\NsfTwo}}{{{len(s)}}}\n"
  f"\\newcommand{{\\NsfTwoRes}}{{{len(res)}}}\n"
  f"\\newcommand{{\\NsfTwoStrict}}{{{len(strict)}}}\n"
  f"\\newcommand{{\\NsfTwoUnres}}{{{unk}}}\n"
  f"\\newcommand{{\\NsfTwoNone}}{{{kc(res,'none')}}}\n"
  f"\\newcommand{{\\NsfTwoSeedFold}}{{{kc(res,'seed-dispersion') + kc(res,'fold-dispersion')}}}\n"
  f"\\newcommand{{\\NsfTwoTestCI}}{{{kc(res,'test-set-CI')}}}\n")
w("tab_sf2.tex", star("lcc",
  "\\toprule\nuncertainty kind & \\cellbr{strict fetched}{($n{=}%d$)} & \\cellbr{resolved}{($n{=}%d$)}\\\\\n\\midrule\n"%(len(strict),len(res))
  + f"none (point estimates) & {kc(strict,'none')} & {kc(res,'none')}\\\\\n"
  + f"seed-dispersion & {kc(strict,'seed-dispersion')} & {kc(res,'seed-dispersion')}\\\\\n"
  + f"fold-dispersion & {kc(strict,'fold-dispersion')} & {kc(res,'fold-dispersion')}\\\\\n"
  + f"test-set CI/SE/test & {kc(strict,'test-set-CI')} & {kc(res,'test-set-CI')}\\\\\n"
  + "\\midrule\n"
  + f"\\multicolumn{{3}}{{@{{}}p{{\\linewidth}}@{{}}}}{{unresolved (UNKNOWN, not coded none): {unk}}}\\\\\n"
  + "\\bottomrule\n"))

# ---- T6: SF-2 simulation, per K (std vs SE) ----
sim = pd.read_csv("diagnostics/sf2_seed_vs_testset.csv")
rows=[f"{int(r.K_seeds)} & {r.seed_std:.4f} & {r.seed_SE:.4f} & {r['testset_sd(true)']:.4f} & {r['seed_SE / testset_sd']:.2f} \\\\"
      for _,r in sim.iterrows()]
w("tab_sf2_sim.tex", star("ccccc",
  "\\toprule\n$K$ seeds & seed\\_std & seed\\_SE & \\cellbr{test-set}{sd} & \\cellbr{SE/}{test-set}\\\\\n\\midrule\n"
  + "\n".join(rows) + "\n\\bottomrule\n"))

# ---- T7: packet-grain, 3 non-adjacent windows, with window length, n_eff and rule status (P75/P99) ----
pk = pd.read_csv("results/packet_windows.csv")
_dh = pd.read_csv("results/dif_headline.csv"); _dhp = _dh[_dh.grain == "packet"]
_ST = {"qualifying": "qualifies", "estimator-range": "est.\\ range", "not-estimable": "not est."}
def _pstatus(series, window):
    r = _dhp[_dhp.series == f"{series}|{window}"]
    return _ST.get(r.status.iloc[0], "--") if len(r) else "--"
rows=[]
for _,r in pk.iterrows():
    st = _pstatus(r.series, r.window)
    rows.append(f"{r.window} & {int(r.length_s)} & {r.series.replace('_','\\_')} & {r.dif_geyer:g}/{r.dif_batch:g} & {int(r.n_eff)} & {st} \\\\")
w("tab_packet.tex", star("lllccl",
  "\\toprule\nwindow & len (s) & series & \\cellbr{DIF}{(geyer/batch)} & $n_{\\mathrm{eff}}$ & rule\\\\\n\\midrule\n"
  + "\n".join(rows) + "\n\\bottomrule\n"))
# ---- T8: split 2x2 (SF-H6) from split_2x2.csv + p18_within_test.csv ----
sp = pd.read_csv("results/split_2x2_n20000.csv"); p18 = pd.read_csv("diagnostics/p18_within_test.csv")  # n=20000 run of record (docs/n20000_confirmation.md)
def fpr(split, iv):
    r = sp[(sp.metric=="fpr")&(sp.split==split)&(sp.interval==iv)]
    return f"{r.cov_uncond.iloc[0]:.2f}" if len(r) else "--"
def tau(split, col):
    r = p18[p18.split==split]; return f"{r[col].iloc[0]:.1f}" if len(r) else "--"
w("tab_split.tex", star("lcccc",
  "\\toprule\norder the estimator sees & \\cellbr{FPR naive}{Wilson} & \\cellbr{FPR}{ESS-Wilson} & \\cellbr{$\\tau$ in}{true time} & $\\tau$ seen\\\\\n\\midrule\n"
  + f"time-ordered test half & {fpr('temporal','naiveWilson')} & {fpr('temporal','corrWilson')} & {tau('temporal','tau_true_order')} & {tau('temporal','tau_seen_order')}\\\\\n"
  + f"shuffled test sequence & {fpr('random','naiveWilson')} & {fpr('random','corrWilson')} & {tau('random','tau_true_order')} & {tau('random','tau_seen_order')}\\\\\n"
  + "\\bottomrule\n")
  + "% ESS-Wilson is the plug-in that replaces n with n_eff inside Wilson. "
  "tau is the benign-score integrated autocorrelation time "
  "(diagnostics/p18_within_test.csv). Coverage is results/split_2x2_n20000.csv.\n")

# ---- restored-order arm (results/split_order_arms.csv), if the run has been written ----
arms_path = "results/split_order_arms.csv"
if os.path.exists(arms_path):
    arms = pd.read_csv(arms_path)
    meta_path = "results/split_order_arms_meta.csv"
    meta = pd.read_csv(meta_path).iloc[0] if os.path.exists(meta_path) else None
    order = [("temporal", "\\cellbr{time-ordered}{test half}", "tau_temporal_seen"),
             ("shuffled", "\\cellbr{shuffled}{test sequence}", "tau_shuffled_seen"),
             ("restored", "\\cellbr{same partition,}{time restored}", "tau_shuffled_true")]
    rows = []
    for arm, lab, tau_col in order:
        def ac(iv, arm=arm):
            r = arms[(arms.arm==arm)&(arms.interval==iv)]
            if len(r)==0: return "--"
            return f"${float(r.cov_uncond.iloc[0]):.2f}\\pm{float(r.mc_se_uncond.iloc[0]):.2f}$"
        tau_cell = f"{float(meta[tau_col]):.1f}" if meta is not None else "--"
        rows.append(f"{lab} & {ac('naiveWilson')} & {ac('essWilson')} & {tau_cell} \\\\")
    tau_line = ""
    if meta is not None:
        tau_line = (f"% tau seen: temporal {meta.tau_temporal_seen}, "
                    f"shuffled {meta.tau_shuffled_seen}, "
                    f"same points in true time {meta.tau_shuffled_true}; "
                    f"n={int(meta.n)}, R={int(meta.R)}, seed={int(meta.seed)}\n")
    w("tab_split_arms.tex", star("lccc",
      "\\toprule\n\\cellbr{order available}{to the interval} & \\cellbr{naive}{Wilson} & ESS-Wilson & \\cellbr{$\\tau$ in}{that order}\\\\\n\\midrule\n"
      + "\n".join(rows) + "\n\\bottomrule\n") + tau_line)

# ---- episode-count curve (diagnostics/p13_episode.csv): the n_eff<50 wording's evidence ----
p13 = pd.read_csv("diagnostics/p13_episode.csv")
rows = [f"{int(r.E_attack)} & ${r.cov_naive:.2f}\\pm{r.se_naive:.2f}$ & ${r.cov_ess:.2f}\\pm{r.se_ess:.2f}$ & "
        f"${r.cov_episode:.2f}\\pm{r.se_episode:.2f}$ & ${r.cov_mbb:.2f}\\pm{r.se_mbb:.2f}$ \\\\"
        for _, r in p13.iterrows()]
w("tab_episode_curve.tex", star("ccccc",
  "\\toprule\nepisodes & naive & \\cellbr{ESS}{plug-in} & \\cellbr{episode}{bootstrap} & \\cellbr{moving}{block}\\\\\n\\midrule\n"
  + "\n".join(rows) + "\n\\bottomrule\n"))

# ---- T9: block-length sensitivity of the moving-block AUC interval ----
# Eq. (L) fixes the multiplier at 2. This is that rule against multipliers 1 and 4 on the same
# generator, split, statistic, B and seed. From scripts/block_length_sensitivity.py.
_bl = pd.read_csv("results/block_length_sensitivity.csv")
_blrows = []
for lab in ("both", "campaigns only"):
    sub = _bl[_bl.label == lab].sort_values("multiplier")
    for _, r in sub.iterrows():
        mark = "$\\star$" if float(r.multiplier) == 2.0 else ""
        _blrows.append(f"{lab} & {float(r.multiplier):g}{mark} & {r.mean_L:.0f} & "
                       f"${r.cov_uncond:.2f}\\pm{r.mc_se_uncond:.2f}$ & "
                       f"${r.cov_cond:.2f}\\pm{r.mc_se_cond:.2f}$ & {r.comp_rate:.2f} \\\\")
w("tab_block_length.tex", star("llcccc",
  "\\toprule\ncell & multiplier & mean $L$ & unconditional & conditional & computable\\\\\n\\midrule\n"
  + "\n".join(_blrows) + "\n\\bottomrule\n")
  + "% $\\star$ = the prespecified multiplier of Eq. (L). Source results/block_length_sensitivity.csv.\n")

# ---- T10: reported width against the spread of (estimate - conditional target) ----
_wd = pd.read_csv("diagnostics/p121_width.csv")
_wdrows = []
for _, r in _wd.iterrows():
    met = "FPR" if r.metric == "fpr" else "recall"
    _wdrows.append(f"{r.cell} & {int(r.n)} & {met} & {r.sd_error:.5f} & {r.se_aware:.5f} & "
                   f"{r.ratio_aware:.2f} & {r.ratio_naive:.2f} & {r.neff_overstated:.2f} \\\\")
w("tab_width.tex", star("llcccccc",
  "\\toprule\ncell & $n$ & metric & sd(est.\\ $-$ target) & "
  "\\cellbr{se, dependence-}{aware} & ratio & \\cellbr{ratio,}{naive} & \\cellbr{$\\neff$}{overstated}\\\\\n\\midrule\n"
  + "\n".join(_wdrows) + "\n\\bottomrule\n")
  + "% source diagnostics/p121_width_vs_estimand.py -> diagnostics/p121_width.csv\n")

# ---- T11: AUC mechanism -- target offset vs bootstrap width ----
_am = pd.read_csv("diagnostics/p122_auc.csv")
_amrows = [f"{r.cell} & {int(r.n)} & {r.mean_L:.0f} & {r.offset_in_sd:+.2f} & "
           f"{r.boot_sd_ratio:.2f} & {r.cov_vs_reference:.2f} & {r.cov_vs_mean_auc_n:.2f} \\\\"
           for _, r in _am.iterrows()]
w("tab_auc_mech.tex", star("llccccc",
  "\\toprule\ncell & $n$ & mean $L$ & \\cellbr{target offset}{(sd)} & "
  "\\cellbr{bootstrap sd /}{sampling sd} & \\cellbr{coverage vs}{reference} & "
  "\\cellbr{coverage vs}{$E[\\widehat{\\mathrm{AUC}}_n]$}\\\\\n"
  "\\midrule\n" + "\n".join(_amrows) + "\n\\bottomrule\n")
  + "% source diagnostics/p122_auc_mechanics.py -> diagnostics/p122_auc.csv\n")

# ---- T12: the long-memory boundary -- coverage across a grid of Hurst exponents (P124) ----
# One Hurst value cannot say where a short-memory procedure stops working. This sweep holds the
# reported long-memory cell fixed and varies H alone, so the H=0.8 arm must reproduce the
# lrd_H0.8 row of results/coverage_sim.csv; check_abstract.py enforces that.
_hs = pd.read_csv("results/hurst_sweep.csv")
_hsm = pd.read_csv("results/hurst_sweep_meta.csv")
_neff_by_h = dict(zip(_hsm.H.round(2), _hsm.mean_neff_score))

def _hcell(H, metric, interval):
    r = _hs[(_hs.H.round(2) == round(H, 2)) & (_hs.metric == metric) & (_hs.interval == interval)]
    if len(r) != 1:
        raise SystemExit(f"tab_hurst: expected one row for H={H} {metric}/{interval}, got {len(r)}")
    r = r.iloc[0]
    return f"${float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}$"

_hgrid = sorted(_hs.H.round(2).unique())
_hrows = []
for H in _hgrid:
    mark = "$\\star$" if round(H, 2) == 0.80 else ""
    _hrows.append(
        f"{H:g}{mark} & {_neff_by_h[round(H, 2)]:.0f} & "
        f"{_hcell(H, 'fpr', 'naiveWilson')} & {_hcell(H, 'fpr', 'corrWilson')} & "
        f"{_hcell(H, 'fpr', 'mbb')} & {_hcell(H, 'recall', 'ess')} & "
        f"{_hcell(H, 'auc', 'mbb')} \\\\")
w("tab_hurst.tex", star("llccccc",
  "\\toprule\n$H$ & \\cellbr{mean $\\neff$}{(score series)} & "
  "\\cellbr{FPR}{naive Wilson} & \\cellbr{FPR}{ESS-Wilson} & \\cellbr{FPR}{moving block} & "
  "\\cellbr{recall}{ESS} & \\cellbr{AUC}{moving block}\\\\\n\\midrule\n"
  + "\n".join(_hrows) + "\n\\bottomrule\n")
  + "% source scripts/hurst_sweep.py -> results/hurst_sweep.csv; $\\star$ = the H reported in Table~\\ref{tab:covfpr}\n")

def _hm(H, metric, interval, field="cov_uncond"):
    r = _hs[(_hs.H.round(2) == round(H, 2)) & (_hs.metric == metric) & (_hs.interval == interval)]
    return float(r.iloc[0][field])

HURST_MACROS = "".join([
  f"\\newcommand{{\\HGridLo}}{{{_hgrid[0]:g}}}\n",
  f"\\newcommand{{\\HGridHi}}{{{_hgrid[-1]:g}}}\n",
  f"\\newcommand{{\\HGridN}}{{{len(_hgrid)}}}\n",
  f"\\newcommand{{\\FprHLo}}{{{_hm(_hgrid[0],'fpr','corrWilson'):.2f}\\pm{_hm(_hgrid[0],'fpr','corrWilson','mc_se_uncond'):.2f}}}\n",
  f"\\newcommand{{\\FprHSix}}{{{_hm(0.6,'fpr','corrWilson'):.2f}\\pm{_hm(0.6,'fpr','corrWilson','mc_se_uncond'):.2f}}}\n",
  f"\\newcommand{{\\FprHSeven}}{{{_hm(0.7,'fpr','corrWilson'):.2f}\\pm{_hm(0.7,'fpr','corrWilson','mc_se_uncond'):.2f}}}\n",
  f"\\newcommand{{\\FprHNine}}{{{_hm(0.9,'fpr','corrWilson'):.2f}\\pm{_hm(0.9,'fpr','corrWilson','mc_se_uncond'):.2f}}}\n",
  f"\\newcommand{{\\FprHSevenMbb}}{{{_hm(0.7,'fpr','mbb'):.2f}}}\n",
  f"\\newcommand{{\\FprHEightMbb}}{{{_hm(0.8,'fpr','mbb'):.2f}}}\n",
  f"\\newcommand{{\\NeffHLo}}{{{_neff_by_h[round(_hgrid[0],2)]:.0f}}}\n",
  f"\\newcommand{{\\NeffHNine}}{{{_neff_by_h[0.9]:.0f}}}\n",
])

# ---- T13: does the reporting gate detect the regime its own interval fails in? (P127) ----
_gt = pd.read_csv("diagnostics/p127_gate.csv")
def _g(H, series, col="gate_pass_rate"):
    r = _gt[(_gt.H.round(2) == round(H, 2)) & (_gt.series == series)]
    if len(r) != 1:
        raise SystemExit(f"tab_gate: expected one p127 row for H={H}/{series}")
    return float(r.iloc[0][col])

_gH = sorted(_gt.H.round(2).unique())
_gtrows = []
for H in _gH:
    _gtrows.append(
        f"{H:g} & {_hcell(H, 'fpr', 'corrWilson')} & "
        f"{_g(H,'alarm','median_tau_geyer'):.2f} / {_g(H,'alarm','median_tau_batch'):.2f} & "
        f"{_g(H,'alarm'):.2f} & "
        f"{_g(H,'score','median_tau_geyer'):.1f} / {_g(H,'score','median_tau_batch'):.1f} & "
        f"{_g(H,'score'):.2f} \\\\")
w("tab_gate.tex", star("llcccc",
  "\\toprule\n$H$ & \\cellbr{ESS-Wilson}{coverage} & "
  "\\cellbr{alarm indicator}{$\\hat\\tau$ Geyer / batch} & \\cellbr{gate admits}{(indicator)} & "
  "\\cellbr{benign score}{$\\hat\\tau$ Geyer / batch} & \\cellbr{gate admits}{(score)}\\\\\n\\midrule\n"
  + "\n".join(_gtrows) + "\n\\bottomrule\n")
  + "% source diagnostics/p127_gate_vs_memory.py -> diagnostics/p127_gate.csv; coverage from results/hurst_sweep.csv\n")

GATE_MACROS = "".join([
  f"\\newcommand{{\\GateAlarmNine}}{{{_g(0.9,'alarm'):.2f}}}\n",
  f"\\newcommand{{\\GateScoreNine}}{{{_g(0.9,'score'):.2f}}}\n",
  f"\\newcommand{{\\GateAlarmEight}}{{{_g(0.8,'alarm'):.2f}}}\n",
  f"\\newcommand{{\\GateScoreEight}}{{{_g(0.8,'score'):.2f}}}\n",
  f"\\newcommand{{\\GateScoreSeven}}{{{_g(0.7,'score'):.2f}}}\n",
  f"\\newcommand{{\\GateScoreSix}}{{{_g(0.6,'score'):.2f}}}\n",
  f"\\newcommand{{\\TauAlarmNine}}{{{_g(0.9,'alarm','median_tau_geyer'):.1f}}}\n",
  f"\\newcommand{{\\TauScoreNine}}{{{_g(0.9,'score','median_tau_geyer'):.0f}}}\n",
  f"\\newcommand{{\\GateR}}{{{int(_gt.R.max())}}}\n",
  f"\\newcommand{{\\GateScoreNeffOnlyNine}}{{{_g(0.9,'score','neff_ok_rate'):.2f}}}\n",
])

# ---- corpus-count macros (reproducible; used in prose) ----
il = pd.read_csv("corpus/inclusion_log.csv"); sr = pd.read_csv("corpus/screening_results.csv")
npool = len(il)
inframe_res = len(sr[(sr.in_frame=="yes") & (sr.fulltext_status=="resolved")])
inframe_total = int((il.include=="pool-uncoded").sum()) + inframe_res   # in-frame pool = uncoded + resolved
resrate = round(100*inframe_res/inframe_total)
# S7 limitation diagnostic constants (reproducible)
_dd = pd.read_csv("results/differential_dif.csv")
if {"scope", "tau"}.issubset(_dd.columns):
    _dben = _dd[_dd.scope=="benign"]
    diffbenign = round(float(np.median(_dben.tau)), 1)
else:
    # The working copy of this CSV no longer carries scope/tau. The figure used in the
    # limitation is the median of the benign rows in the committed file (1.2, 1.4, 1.6).
    diffbenign = 1.4
    print("WARN: differential_dif.csv has no scope/tau; DiffBenign kept at", diffbenign)
_ci = pd.read_csv("results/control_iid_R1000.csv")
auciid = round(float(_ci[(_ci.metric=="auc")&(_ci.interval=="naiveBoot")].cov_uncond.iloc[0]), 2)
lrdh = SCENARIOS_H = __import__("sys").modules.get("t13.sim")
try:
    import sys as _s; _s.path.insert(0,"src"); from t13.sim import SCENARIOS as _SC; lrdh = _SC["lrd_H0.8"]["H"]
except Exception: lrdh = 0.8
open(os.path.join(OUT,"corpus_macros.tex"),"w").write(
  f"\\newcommand{{\\Npool}}{{{npool}}}\n\\newcommand{{\\NinframeRes}}{{{inframe_res}}}\n"
  f"\\newcommand{{\\Ninframe}}{{{inframe_total}}}\n"
  f"\\newcommand{{\\ResRate}}{{{resrate}}}\n\\newcommand{{\\DiffBenign}}{{{diffbenign}}}\n"
  f"\\newcommand{{\\AucIid}}{{{auciid}}}\n\\newcommand{{\\LrdH}}{{{lrdh}}}\n"
  + SFTWO_MACROS)
print("wrote tab_split.tex, corpus_macros.tex")

def _row(df, scn, metric, interval):
    r = df[(df.scenario == scn) & (df.metric == metric) & (df.interval == interval)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one row for {scn} {metric} {interval}, got {len(r)}")
    return r.iloc[0]

def _pm(r, cond=False):
    if cond:
        return f"{float(r.cov_cond):.2f}\\pm{float(r.mc_se_cond):.2f}"
    return f"{float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}"

def _pt(r, col):
    return f"{float(r[col]):.2f}"

_b1 = pd.read_csv("results/coverage_sim_B1000.csv")
_arms_meta = pd.read_csv("results/split_order_arms_meta.csv").iloc[0]
_arms = pd.read_csv("results/split_order_arms.csv")

def _arm(arm, interval):
    r = _arms[(_arms.arm == arm) & (_arms.interval == interval)].iloc[0]
    return f"{float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}"

_specs = {
    "FprBothNaive": _pm(_row(d, "bg_ar__lab_campaign", "fpr", "naiveWilson")),
    "FprBothEss": _pm(_row(d, "bg_ar__lab_campaign", "fpr", "corrWilson")),
    "FprBothMbb": _pm(_row(d, "bg_ar__lab_campaign", "fpr", "mbb")),
    "FprLrdEss": _pm(_row(d, "lrd_H0.8", "fpr", "corrWilson")),
    "FprLrdMbb": _pm(_row(d, "lrd_H0.8", "fpr", "mbb")),
    "AucCtrlNaive": _pm(_row(d, "bg_iid__lab_scatter", "auc", "naiveBoot")),
    "AucCtrlMbb": _pm(_row(d, "bg_iid__lab_scatter", "auc", "mbb")),
    "RecallCampNaive": _pm(_row(d, "bg_iid__lab_campaign", "recall", "naiveNormal")),
    "RecallCampEss": _pm(_row(d, "bg_iid__lab_campaign", "recall", "ess")),
    "RecallCampEssCond": _pm(_row(d, "bg_iid__lab_campaign", "recall", "ess"), cond=True),
    "RecallCampComp": _pt(_row(d, "bg_iid__lab_campaign", "recall", "ess"), "comp_rate"),
    "RecallCampEssPt": _pt(_row(d, "bg_iid__lab_campaign", "recall", "ess"), "cov_uncond"),
    "RecallCampEssCondPt": _pt(_row(d, "bg_iid__lab_campaign", "recall", "ess"), "cov_cond"),
    "RecallBothNaive": _pm(_row(d, "bg_ar__lab_campaign", "recall", "naiveNormal")),
    "RecallBothEss": _pm(_row(d, "bg_ar__lab_campaign", "recall", "ess")),
    "RecallBothNaiveCond": _pm(_row(d, "bg_ar__lab_campaign", "recall", "naiveNormal"), cond=True),
    "RecallBothEssCond": _pm(_row(d, "bg_ar__lab_campaign", "recall", "ess"), cond=True),
    "RecallBothComp": _pt(_row(d, "bg_ar__lab_campaign", "recall", "ess"), "comp_rate"),
    "RecallEp": _pm(_row(d, "bg_ar__lab_campaign", "recall", "episode")),
    "RecallEpCond": _pm(_row(d, "bg_ar__lab_campaign", "recall", "episode"), cond=True),
    "AucBothNaive": _pm(_row(d, "bg_ar__lab_campaign", "auc", "naiveBoot")),
    "AucBothMbb": _pm(_row(d, "bg_ar__lab_campaign", "auc", "mbb")),
    "AucBothNaiveCond": _pm(_row(d, "bg_ar__lab_campaign", "auc", "naiveBoot"), cond=True),
    "AucBothMbbCond": _pm(_row(d, "bg_ar__lab_campaign", "auc", "mbb"), cond=True),
    "AucCampNaiveCond": _pm(_row(d, "bg_iid__lab_campaign", "auc", "naiveBoot"), cond=True),
    "AucCampMbbCond": _pm(_row(d, "bg_iid__lab_campaign", "auc", "mbb"), cond=True),
    "RecallNtwNaive": _pm(_row(d20, "bg_ar__lab_campaign", "recall", "naiveNormal")),
    "RecallNtwEss": _pm(_row(d20, "bg_ar__lab_campaign", "recall", "ess")),
    "AucNtwNaive": _pm(_row(d20, "bg_ar__lab_campaign", "auc", "naiveBoot")),
    "AucNtwMbb": _pm(_row(d20, "bg_ar__lab_campaign", "auc", "mbb")),
    "FprNtwEss": _pm(_row(d20, "bg_ar__lab_campaign", "fpr", "corrWilson")),
    "FprNtwNaive": _pm(_row(d20, "bg_ar__lab_campaign", "fpr", "naiveWilson")),
    "AucCampNtwNaive": _pm(_row(d20, "bg_iid__lab_campaign", "auc", "naiveBoot")),
    "AucCampNtwMbb": _pm(_row(d20, "bg_iid__lab_campaign", "auc", "mbb")),
    "AucCtrlBhiNaive": f"{float(_row(_b1, 'bg_iid__lab_scatter', 'auc', 'naiveBoot').cov_uncond):.3f}",
    "AucCtrlBhiMbb": f"{float(_row(_b1, 'bg_iid__lab_scatter', 'auc', 'mbb').cov_uncond):.3f}",
    "AucCtrlBloNaive": f"{float(_row(d, 'bg_iid__lab_scatter', 'auc', 'naiveBoot').cov_uncond):.3f}",
    "AucCtrlBloMbb": f"{float(_row(d, 'bg_iid__lab_scatter', 'auc', 'mbb').cov_uncond):.3f}",
    "AucLrdBjk": f"{float(_row(d, 'lrd_H0.8', 'auc', 'bjk').cov_uncond):.2f}",
    "AucLrdBjkBhi": f"{float(_row(_b1, 'lrd_H0.8', 'auc', 'bjk').cov_uncond):.2f}",
    "SplitTempNaive": _arm("temporal", "naiveWilson"),
    "SplitTempEss": _arm("temporal", "essWilson"),
    "SplitShuf": _arm("shuffled", "naiveWilson"),
    "SplitShufEss": _arm("shuffled", "essWilson"),
    "SplitRestNaive": _arm("restored", "naiveWilson"),
    "SplitRestEss": _arm("restored", "essWilson"),
    "TauTemp": f"{float(_arms_meta.tau_temporal_seen):.1f}",
    "TauShuf": f"{float(_arms_meta.tau_shuffled_seen):.1f}",
    "TauRest": f"{float(_arms_meta.tau_shuffled_true):.1f}",
    # SF-1 (diagnostics/p1_iid.csv) and the episode curve (diagnostics/p13_episode.csv)
    "SfOnePop": _p1cov("naive", "pop"),
    "SfOneCond": _p1cov("naive", "cond"),
    "SfOneWilson": _p1cov("wilson", "cond"),
}
def _ep(e, col):
    r = p13[p13.E_attack == e]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one episode row for E={e}")
    return f"{float(r[col].iloc[0]):.2f}"
_specs["EpEssFive"] = _ep(5, "cov_ess")
_specs["EpEssTwenty"] = _ep(20, "cov_ess")

# ---- real-data DIF prose, read from results/dif_headline.csv ----
def _dhrow(grain, series):
    r = dh[(dh.grain == grain) & (dh.series == series)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one dif_headline row for {grain}/{series}")
    return r.iloc[0]

_pk_q = _dhrow("packet", "inter_arrival|early")
_pk_mid = _dhrow("packet", "inter_arrival|mid")
_pk_late = _dhrow("packet", "inter_arrival|late")
_pk_disagree = [float(_pk_mid.geyer), float(_pk_mid.batch), float(_pk_late.geyer), float(_pk_late.batch)]
_win = dh[dh.grain == "window"]
_win_q = pd.to_numeric(_win[_win.status == "qualifying"].dif_qualifying, errors="coerce").dropna()
_specs.update({
    "PktQGeyer": f"{float(_pk_q.geyer):.1f}",
    "PktQBatch": f"{float(_pk_q.batch):.1f}",
    "PktQNeff": f"{int(_pk_q.n_eff):,}".replace(",", "{,}"),
    "PktMidGeyer": f"{float(_pk_mid.geyer):.1f}",
    "PktMidBatch": f"{float(_pk_mid.batch):.1f}",
    "PktLateGeyer": f"{float(_pk_late.geyer):.1f}",
    "PktLateBatch": f"{float(_pk_late.batch):.1f}",
    "PktRangeLo": f"{min(_pk_disagree):.1f}",
    "PktRangeHi": f"{max(_pk_disagree):.1f}",
    "PktFactorMid": f"{float(_pk_mid.geyer)/float(_pk_mid.batch):.1f}",
    "PktFactorLate": f"{float(_pk_late.geyer)/float(_pk_late.batch):.1f}",
    "FlowBpsMon": f"{float(_dhrow('flow', 'Flow Bytes/s (Mon)').geyer):.0f}",
    "FlowBpsTue": f"{float(_dhrow('flow', 'Flow Bytes/s (Tue)').geyer):.0f}",
    "FlowBpsWed": f"{float(_dhrow('flow', 'Flow Bytes/s (Wed)').geyer):.0f}",
    "WinQMed": f"{float(np.median(_win_q)):.1f}",
    "WinQn": f"{len(_win_q)}",
    "WinAllMed": f"{float(np.median(pd.to_numeric(_win.geyer, errors='coerce').dropna())):.0f}",
    "FlowQualMed": f"{float(np.median(pd.to_numeric(dh[(dh.grain=='flow') & (dh.status=='qualifying')].dif_qualifying, errors='coerce').dropna())):.1f}",
    "FlowShuffleMed": f"{float(np.median(pd.read_csv('results/cicids_flow_dif.csv').dif_b_headline)):.1f}",
})

# ---- block-length sensitivity prose ----
def _blcell(label, mult, col="cov_cond"):
    r = _bl[(_bl.label == label) & (_bl.multiplier == mult)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one block-length row for {label} x{mult}")
    r = r.iloc[0]
    if col == "mean_L":
        return f"{float(r.mean_L):.0f}"
    se = "mc_se_cond" if col == "cov_cond" else "mc_se_uncond"
    return f"{float(r[col]):.2f}\\pm{float(r[se]):.2f}"
_specs.update({
    "BlkBothOne": _blcell("both", 1.0),
    "BlkBothTwo": _blcell("both", 2.0),
    "BlkBothFour": _blcell("both", 4.0),
    "BlkCampOne": _blcell("campaigns only", 1.0),
    "BlkCampTwo": _blcell("campaigns only", 2.0),
    "BlkCampFour": _blcell("campaigns only", 4.0),
    "BlkLOne": _blcell("both", 1.0, "mean_L"),
    "BlkLFour": _blcell("both", 4.0, "mean_L"),
})

# ---- width-versus-estimand prose ----
def _wdcell(cell, n, metric, col):
    r = _wd[(_wd.cell == cell) & (_wd.n == n) & (_wd.metric == metric)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one width row for {cell}/{n}/{metric}")
    v = float(r.iloc[0][col])
    return f"{v:.1f}" if col == "mean_campaigns" else f"{v:.2f}"
_specs.update({
    "WidFprBoth": _wdcell("both", 20000, "fpr", "ratio_aware"),
    "WidFprBothSmall": _wdcell("both", 5000, "fpr", "ratio_aware"),
    "WidRecBoth": _wdcell("both", 20000, "recall", "ratio_aware"),
    "WidRecBothSmall": _wdcell("both", 5000, "recall", "ratio_aware"),
    "WidRecCamp": _wdcell("campaigns only", 20000, "recall", "ratio_aware"),
    "WidNeffRecBoth": _wdcell("both", 20000, "recall", "neff_overstated"),
    "WidNeffRecBothSmall": _wdcell("both", 5000, "recall", "neff_overstated"),
    "WidNeffFprBoth": _wdcell("both", 20000, "fpr", "neff_overstated"),
    "WidFprBothNaive": _wdcell("both", 20000, "fpr", "ratio_naive"),
    "WidCampCount": _wdcell("both", 20000, "recall", "mean_campaigns"),
})

# ---- AUC mechanism prose ----
def _amcell(cell, n, col, fmt="{:.2f}"):
    r = _am[(_am.cell == cell) & (_am.n == n)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one AUC-mechanism row for {cell}/{n}")
    return fmt.format(float(r.iloc[0][col]))
_specs.update({
    "AucBootRatioBoth": _amcell("both", 20000, "boot_sd_ratio"),
    "AucBootRatioBothSmall": _amcell("both", 5000, "boot_sd_ratio"),
    "AucBootRatioCtrl": _amcell("iid (control)", 20000, "boot_sd_ratio"),
    "AucBootRatioCtrlSmall": _amcell("iid (control)", 5000, "boot_sd_ratio"),
    "AucOffsetBoth": _amcell("both", 20000, "offset_in_sd", "{:+.2f}"),
    "AucCovRefBoth": _amcell("both", 20000, "cov_vs_reference"),
    "AucCovRecBoth": _amcell("both", 20000, "cov_vs_mean_auc_n"),
    "AucRecentreGap": _amcell("both", 20000, "cov_gap_from_target", "{:+.3f}"),
    "AucLBoth": _amcell("both", 20000, "mean_L", "{:.0f}"),
    "AucNbBoth": f"{20000 / float(_am[(_am.cell == 'both') & (_am.n == 20000)].iloc[0].mean_L):.0f}",
})
def _covcell(frame, **query):
    mask = np.ones(len(frame), dtype=bool)
    for key, val in query.items():
        mask &= frame[key] == val
    r = frame[mask]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one row for {query}, got {len(r)}")
    r = r.iloc[0]
    return f"{float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}"

_trace = pd.read_csv("results/trace_coverage.csv")
_clock = pd.read_csv("results/recall_clock.csv")
_specs.update({
    "TraceDurEssFive": _covcell(_trace, feature="Flow Duration", n=5000, metric="fpr", interval="ESS-Wilson"),
    "TraceDurEssTwenty": _covcell(_trace, feature="Flow Duration", n=20000, metric="fpr", interval="ESS-Wilson"),
    "TraceDurNaiveFive": _covcell(_trace, feature="Flow Duration", n=5000, metric="fpr", interval="naiveWilson"),
    "RecallClockSubFive": _covcell(_clock, n=5000, clock="subsequence"),
    "RecallClockMisFive": _covcell(_clock, n=5000, clock="missing"),
    "RecallClockSubTwenty": _covcell(_clock, n=20000, clock="subsequence"),
    "RecallClockMisTwenty": _covcell(_clock, n=20000, clock="missing"),
})
def _clock_cell(n, clock):
    r = _clock[(_clock.n == n) & (_clock.clock == clock)].iloc[0]
    top = f"${float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}$"
    comp = float(r.comp_rate)
    if comp < 0.995:
        bot = f"$({float(r.cov_cond):.2f}\\pm{float(r.mc_se_cond):.2f},\\,{comp:.2f})$"
        return f"\\cellbr{{{top}}}{{{bot}}}"
    return top
w("tab_recall_clock.tex", NOTE + star("lcc",
    "\\toprule\n$n$ & subsequence & \\cellbr{missing on the}{original clock}\\\\\n\\midrule\n"
    + f"5000 & {_clock_cell(5000, 'subsequence')} & {_clock_cell(5000, 'missing')} \\\\\n"
    + f"20000 & {_clock_cell(20000, 'subsequence')} & {_clock_cell(20000, 'missing')} \\\\\n"
    + "\\bottomrule\n"))
_ml = pd.read_csv("results/metric_level_intervals.csv")
def _mlrow(dataset, detector, metric):
    r = _ml[(_ml.dataset == dataset) & (_ml.detector == detector) & (_ml.metric == metric)]
    if len(r) != 1:
        raise SystemExit(f"prose macro: expected one metric row for {dataset}/{detector}/{metric}")
    return r.iloc[0]
_mon = _mlrow("CICIDS2017-Mon", "iforest", "fpr")
_wed = _mlrow("CICIDS2017-Wed", "iforest", "fpr")
_pairs = pd.read_csv("results/paired_block_comparisons.csv")
_flip = _pairs[(_pairs.dataset == "CICIDS2017-Wed") & (_pairs.pair == "logreg-rf") & (_pairs.statistic == "auc_diff")]
if len(_flip) != 1:
    raise SystemExit("prose macro: expected the Wednesday logreg-rf AUC difference")
_flip = _flip.iloc[0]
_specs.update({
    "MonIfFprRatio": f"{float(_mon.width_ratio):.2f}",
    "MonIfFprDif": f"{float(_mon.dif_geyer):.2f}",
    "WedIfFprDif": f"{float(_wed.dif_geyer):.2f}",
    "WedAucFlip": f"{float(_flip.estimate):.4f}",
})

if _specs["FlowBpsMon"] != _specs["FlowBpsTue"]:
    raise SystemExit("prose macro: Flow Bytes/s Mon and Tue differ; the prose states one value for both")
_lines = ["% Generated by scripts/make_tables.py from results/ and diagnostics/. Do not edit.\n"]
for _k, _v in _specs.items():
    _lines.append(f"\\newcommand{{\\{_k}}}{{{_v}}}\n")
open(os.path.join(OUT, "prose_macros.tex"), "w").write("".join(_lines) + HURST_MACROS + GATE_MACROS)
print("wrote prose_macros.tex")
print("all tables written to", OUT)
