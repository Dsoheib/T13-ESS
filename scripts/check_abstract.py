"""Residual-2 guard: assert the abstract's hand-restated figures match the generated tables under
the estimator-agreement rule (P99). Fails loudly (exit 1) on mismatch. Run by `make all`.
Sources: results/dif_headline.csv (per-series rule outcome) + results/cicids_flow_dif.csv.
"""
import sys, re, math, pandas as pd, numpy as np
ab = open("paper/main.tex").read()
ab = ab[ab.index("\\begin{abstract}"):ab.index("\\end{abstract}")]
ab = re.sub(r"\s+", " ", ab)  # flatten line wraps so phrases match across breaks
def need(cond, msg):
    if not cond: print("ABSTRACT-CHECK FAIL:", msg); sys.exit(1)

dh = pd.read_csv("results/dif_headline.csv")
def qmed(grain):
    q = pd.to_numeric(dh[(dh.grain == grain) & (dh.status == "qualifying")].dif_qualifying, errors="coerce").dropna()
    return float(np.median(q)) if len(q) else float("nan")

# Qualifying medians stay in the body via macros. The abstract no longer restates them.
pk_q = qmed("packet")
_pk_ia_rng = dh[(dh.grain == "packet") & (dh.status == "estimator-range") & dh.series.str.startswith("inter_arrival")]
pk_rng_hi = float(pd.to_numeric(_pk_ia_rng.geyer, errors="coerce").max())
cf = pd.read_csv("results/cicids_flow_dif.csv"); fm = float(np.median(cf.dif_b_headline))
win_q = qmed("window")
win_all = float(np.median(pd.to_numeric(dh[dh.grain == "window"].geyer, errors="coerce").dropna()))
need(round(pk_q) == 2, f"packet qualifying median {pk_q} is no longer ~2")
need(150 <= pk_rng_hi <= 170, f"packet range upper {pk_rng_hi} left the ~160 band")
need(3.0 <= win_q <= 4.0, f"window qualifying median {win_q} left ~3.5")
need(90 <= win_all <= 102, f"window all-feature median {win_all} left ~96")

# Coverage prose is generated macros. The abstract and the body must use them, and the
# macro file must match a fresh rounding of the CSVs (scripts/make_tables.py is the writer).
import pathlib
macros = pathlib.Path("paper/tables/prose_macros.tex").read_text()
body = open("paper/main.tex").read()
need("\\input{tables/prose_macros.tex}" in body, "prose_macros.tex is not input")
for token in ("RecallNtwEss", "AucNtwMbb", "AucCampNaiveCond", "AucCampMbbCond",
              "FprBothEss", "FprLrdEss", "SplitTempEss", "TauTemp", "TauRest"):
    need("\\" + token in body, f"\\{token} missing from manuscript")
    need(f"\\newcommand{{\\{token}}}" in macros, f"\\{token} missing from prose_macros.tex")
# Reject a hand-typed copy of the n=20000 headline next to the macro.
need("$0.88\\pm0.01$" not in body and "$0.86\\pm0.01$" not in body,
     "hand-typed 0.88/0.86 remains; use the generated macros")

def _pm(frame, scn, metric, interval, cond=False):
    r = frame[(frame.scenario == scn) & (frame.metric == metric) & (frame.interval == interval)]
    need(len(r) == 1, f"expected one coverage row for {scn} {metric} {interval}")
    r = r.iloc[0]
    cov, se = (r.cov_cond, r.mc_se_cond) if cond else (r.cov_uncond, r.mc_se_uncond)
    return f"{float(cov):.2f}\\pm{float(se):.2f}"

_d = pd.read_csv("results/coverage_sim.csv")
_d20 = pd.read_csv("results/coverage_sim_n20000.csv")
_expect = {
    "FprBothEss": _pm(_d, "bg_ar__lab_campaign", "fpr", "corrWilson"),
    "FprLrdEss": _pm(_d, "lrd_H0.8", "fpr", "corrWilson"),
    "AucCampNaiveCond": _pm(_d, "bg_iid__lab_campaign", "auc", "naiveBoot", cond=True),
    "AucCampMbbCond": _pm(_d, "bg_iid__lab_campaign", "auc", "mbb", cond=True),
    "RecallNtwEss": _pm(_d20, "bg_ar__lab_campaign", "recall", "ess"),
    "AucNtwMbb": _pm(_d20, "bg_ar__lab_campaign", "auc", "mbb"),
}
_arms = pd.read_csv("results/split_order_arms.csv")
_meta = pd.read_csv("results/split_order_arms_meta.csv").iloc[0]
_tr = _arms[(_arms.arm == "temporal") & (_arms.interval == "essWilson")].iloc[0]
_expect["SplitTempEss"] = f"{float(_tr.cov_uncond):.2f}\\pm{float(_tr.mc_se_uncond):.2f}"
_expect["TauTemp"] = f"{float(_meta.tau_temporal_seen):.1f}"
_expect["TauRest"] = f"{float(_meta.tau_shuffled_true):.1f}"

# SF-1 threshold mismatch and the episode curve: prose read from the diagnostic runs.
_p1 = pd.read_csv("diagnostics/p1_iid.csv")
def _p1cov(interval, estimand):
    r = _p1[(_p1.metric == "fpr") & (_p1.interval == interval) & (_p1.estimand == estimand)]
    need(len(r) == 1, f"expected one p1_iid row for fpr/{interval}/{estimand}")
    return f"{float(r.coverage.iloc[0]):.2f}"
_expect["SfOnePop"] = _p1cov("naive", "pop")
_expect["SfOneCond"] = _p1cov("naive", "cond")
_p13 = pd.read_csv("diagnostics/p13_episode.csv")
for _name, _E in (("EpEssFive", 5), ("EpEssTwenty", 20)):
    _r = _p13[_p13.E_attack == _E]
    need(len(_r) == 1, f"expected one episode row for E={_E}")
    _expect[_name] = f"{float(_r.cov_ess.iloc[0]):.2f}"

# Real-data DIF prose: every figure comes from the QC-filtered per-series file.
def _dhrow(grain, series):
    r = dh[(dh.grain == grain) & (dh.series == series)]
    need(len(r) == 1, f"expected one dif_headline row for {grain}/{series}")
    return r.iloc[0]
_pkq = _dhrow("packet", "inter_arrival|early")
_expect["PktQGeyer"] = f"{float(_pkq.geyer):.1f}"
_expect["PktQBatch"] = f"{float(_pkq.batch):.1f}"
_expect["FlowBpsWed"] = f"{float(_dhrow('flow', 'Flow Bytes/s (Wed)').geyer):.0f}"
_expect["WinQMed"] = f"{win_q:.1f}"
_expect["WinAllMed"] = f"{win_all:.0f}"
_flow_q = pd.to_numeric(dh[(dh.grain == "flow") & (dh.status == "qualifying")].dif_qualifying, errors="coerce").dropna()
_expect["FlowQualMed"] = f"{float(np.median(_flow_q)):.1f}"

# Width-versus-estimand prose.
_wd = pd.read_csv("diagnostics/p121_width.csv")
def _wdcell(cell, n, metric, col):
    r = _wd[(_wd.cell == cell) & (_wd.n == n) & (_wd.metric == metric)]
    need(len(r) == 1, f"expected one width row for {cell}/{n}/{metric}")
    v = float(r.iloc[0][col])
    return f"{v:.1f}" if col == "mean_campaigns" else f"{v:.2f}"
_expect["WidFprBoth"] = _wdcell("both", 20000, "fpr", "ratio_aware")
_expect["WidRecBoth"] = _wdcell("both", 20000, "recall", "ratio_aware")
_expect["WidRecCamp"] = _wdcell("campaigns only", 20000, "recall", "ratio_aware")
_expect["WidNeffRecBoth"] = _wdcell("both", 20000, "recall", "neff_overstated")
# The interpretive sentences around Table~\ref{tab:width} read the FPR ratio as near one and the
# recall ratio as below one. That is a claim about the science, not about provenance, so a
# regeneration that reverses it is a reason to rewrite the paragraph, not a broken build. Warn.
_wfpr = float(_wdcell("both", 20000, "fpr", "ratio_aware"))
_wrec = float(_wdcell("both", 20000, "recall", "ratio_aware"))
if not (_wfpr > 0.9 and _wrec < 0.9):
    print(f"WARNING: width ratios are now FPR {_wfpr} / recall {_wrec}. The prose around "
          f"tab:width reads the first as near one and the second as short of one. "
          f"Reread that paragraph; this is not a build failure.", file=sys.stderr)

# AUC mechanism prose.
_am = pd.read_csv("diagnostics/p122_auc.csv")
def _amcell(cell, n, col, fmt="{:.2f}"):
    r = _am[(_am.cell == cell) & (_am.n == n)]
    need(len(r) == 1, f"expected one AUC-mechanism row for {cell}/{n}")
    return fmt.format(float(r.iloc[0][col]))
_expect["AucBootRatioBoth"] = _amcell("both", 20000, "boot_sd_ratio")
_expect["AucCovRefBoth"] = _amcell("both", 20000, "cov_vs_reference")
_expect["AucCovRecBoth"] = _amcell("both", 20000, "cov_vs_mean_auc_n")
_expect["AucRecentreGap"] = _amcell("both", 20000, "cov_gap_from_target", "{:+.3f}")
_expect["AucLBoth"] = _amcell("both", 20000, "mean_L", "{:.0f}")
_expect["AucNbBoth"] = f"{20000 / float(_am[(_am.cell == 'both') & (_am.n == 20000)].iloc[0].mean_L):.0f}"
# Cross-run provenance: in the n=20000 dependent cell nearly every replicate is computable, so the
# mechanism run's coverage must reproduce the reported moving-block cell.
_amr = _am[(_am.cell == "both") & (_am.n == 20000)].iloc[0]
_hdl = _d20[(_d20.scenario == "bg_ar__lab_campaign") & (_d20.metric == "auc") &
            (_d20.interval == "mbb")].iloc[0]
_se_mech = math.sqrt(0.25 / float(_amr.reps))
_gap = abs(float(_amr.cov_vs_reference) - float(_hdl.cov_uncond))
_tol = 2 * math.hypot(_se_mech, float(_hdl.mc_se_uncond))
need(_gap <= _tol,
     f"AUC mechanism run gives {_amr.cov_vs_reference} vs reported {_hdl.cov_uncond}, "
     f"gap {_gap:.3f} > 2 combined SE {_tol:.3f}")

# Block-length sensitivity prose.
_bl = pd.read_csv("results/block_length_sensitivity.csv")
def _blcell(label, mult):
    r = _bl[(_bl.label == label) & (_bl.multiplier == mult)]
    need(len(r) == 1, f"expected one block-length row for {label} x{mult}")
    r = r.iloc[0]
    return f"{float(r.cov_cond):.2f}\\pm{float(r.mc_se_cond):.2f}"
for _name, _lab, _m in (("BlkBothTwo", "both", 2.0), ("BlkCampOne", "campaigns only", 1.0),
                        ("BlkCampFour", "campaigns only", 4.0)):
    _expect[_name] = _blcell(_lab, _m)
# The multiplier-2 arm must stay consistent with the headline AUC cells it re-runs.
for _lab, _scn in (("both", "bg_ar__lab_campaign"), ("campaigns only", "bg_iid__lab_campaign")):
    _b = _bl[(_bl.label == _lab) & (_bl.multiplier == 2.0)].iloc[0]
    _h = _d[(_d.scenario == _scn) & (_d.metric == "auc") & (_d.interval == "mbb")].iloc[0]
    _gap = abs(float(_b.cov_cond) - float(_h.cov_cond))
    _tol = 2 * math.hypot(float(_b.mc_se_cond), float(_h.mc_se_cond))
    need(_gap <= _tol,
         f"block-length multiplier-2 arm ({_lab}) is {_b.cov_cond} vs headline {_h.cov_cond}, "
         f"gap {_gap:.3f} > 2 combined SE {_tol:.3f}")

# ---- Hurst sweep: the H=0.8 arm must reproduce the reported long-memory cell ----
# Same generator, n, R, B and seed, with H the only thing varied, so this is an equality check,
# not a Monte Carlo comparison. If it ever stops holding, the sweep is not the same experiment
# and the boundary prose in the paper is not about the reported cell.
_hs = pd.read_csv("results/hurst_sweep.csv")
_hsm = pd.read_csv("results/hurst_sweep_meta.csv")
def _hrow(H, metric, interval):
    r = _hs[(_hs.H.round(2) == round(H, 2)) & (_hs.metric == metric) & (_hs.interval == interval)]
    need(len(r) == 1, f"expected one hurst_sweep row for H={H} {metric}/{interval}")
    return r.iloc[0]
for _metric_name, _iv in (("fpr", "naiveWilson"), ("fpr", "corrWilson"), ("fpr", "mbb"),
                          ("recall", "ess"), ("auc", "mbb")):
    _a = _hrow(0.8, _metric_name, _iv)
    _b = _d[(_d.scenario == "lrd_H0.8") & (_d.metric == _metric_name) & (_d.interval == _iv)]
    need(len(_b) == 1, f"expected one coverage_sim lrd_H0.8 row for {_metric_name}/{_iv}")
    _b = _b.iloc[0]
    need(float(_a.cov_uncond) == float(_b.cov_uncond),
         f"hurst sweep H=0.8 {_metric_name}/{_iv} is {_a.cov_uncond} but the reported cell is "
         f"{_b.cov_uncond}; the sweep is not re-running the same experiment")
# The paper says the degradation is monotone in H. If a rerun breaks that, the prose must change.
_hg = sorted(_hs.H.round(2).unique())
_hcov = [float(_hrow(H, "fpr", "corrWilson").cov_uncond) for H in _hg]
need(all(a >= b for a, b in zip(_hcov, _hcov[1:])),
     f"ESS-Wilson coverage is not monotone decreasing in H ({dict(zip(_hg, _hcov))}); "
     f"rewrite the monotonicity sentence in the long-memory subsection")
_hneff = [float(_hsm[_hsm.H.round(2) == round(H, 2)].mean_neff_score.iloc[0]) for H in _hg]
need(all(a >= b for a, b in zip(_hneff, _hneff[1:])),
     f"mean n_eff is not monotone decreasing in H ({dict(zip(_hg, _hneff))}); "
     f"rewrite the mechanism paragraph")
need("degradation is monotone" in body, "long-memory monotonicity sentence missing")
def _hfmt(H, metric, interval):
    r = _hrow(H, metric, interval)
    return f"{float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}"
_expect["FprHLo"] = _hfmt(_hg[0], "fpr", "corrWilson")
_expect["FprHSix"] = _hfmt(0.6, "fpr", "corrWilson")
_expect["FprHSeven"] = _hfmt(0.7, "fpr", "corrWilson")
_expect["FprHNine"] = _hfmt(0.9, "fpr", "corrWilson")
_expect["FprHSevenMbb"] = f"{float(_hrow(0.7, 'fpr', 'mbb').cov_uncond):.2f}"
_expect["FprHEightMbb"] = f"{float(_hrow(0.8, 'fpr', 'mbb').cov_uncond):.2f}"
_expect["HGridN"] = str(len(_hg))
# The reversal sentence: the plug-in leads at H=0.7 and the moving block leads at H=0.8.
need(float(_hrow(0.7, "fpr", "corrWilson").cov_uncond) > float(_hrow(0.7, "fpr", "mbb").cov_uncond)
     and float(_hrow(0.8, "fpr", "mbb").cov_uncond) > float(_hrow(0.8, "fpr", "corrWilson").cov_uncond),
     "the plug-in/moving-block ordering no longer reverses between H=0.7 and H=0.8; "
     "rewrite the reversal sentence")

# ---- the reporting gate must actually screen the regime it claims to (P127) ----
# The paper's headline recommendation now depends on two orderings: the alarm-indicator gate
# admits the long-memory cells, and the score-series gate does not. If either stops holding the
# recommendation is wrong and this must fail before the PDF is built.
_gt = pd.read_csv("diagnostics/p127_gate.csv")
def _gate(H, series, col="gate_pass_rate"):
    r = _gt[(_gt.H.round(2) == round(H, 2)) & (_gt.series == series)]
    need(len(r) == 1, f"expected one p127 row for H={H}/{series}")
    return float(r.iloc[0][col])
need(_gate(0.9, "alarm") >= 0.85,
     f"the alarm-indicator gate now rejects long memory ({_gate(0.9,'alarm')}); the paper says it "
     f"admits it, so the gate paragraph and the reporting rule must be rewritten")
need(_gate(0.9, "score") <= 0.25,
     f"the score-series gate now admits long memory ({_gate(0.9,'score')}); the reporting rule "
     f"rests on it rejecting that regime")
need(_gate(0.6, "score") >= 0.95,
     f"the score-series gate now rejects the short-memory cells ({_gate(0.6,'score')}); a gate that "
     f"rejects the regime where the interval works is not usable")
_ga = [_gate(H, "alarm") for H in (0.55, 0.6, 0.7, 0.8, 0.9)]
_gs = [_gate(H, "score") for H in (0.55, 0.6, 0.7, 0.8, 0.9)]
need(all(a >= b for a, b in zip(_gs, _gs[1:])),
     f"the score-series gate is not monotone decreasing in H ({_gs})")
need(all(a >= s for a, s in zip(_ga, _gs)),
     f"the alarm gate is not uniformly more permissive than the score gate ({_ga} vs {_gs})")
_expect["GateAlarmNine"] = f"{_gate(0.9,'alarm'):.2f}"
_expect["GateScoreNine"] = f"{_gate(0.9,'score'):.2f}"
_expect["GateAlarmEight"] = f"{_gate(0.8,'alarm'):.2f}"
_expect["GateScoreEight"] = f"{_gate(0.8,'score'):.2f}"
_expect["GateScoreSeven"] = f"{_gate(0.7,'score'):.2f}"
_expect["GateScoreSix"] = f"{_gate(0.6,'score'):.2f}"
need("must be read on the benign score series" in ab,
     "the abstract no longer states which series the gate is read on")

_trace = pd.read_csv("results/trace_coverage.csv")
def _tcell(feature, n, metric, interval):
    r = _trace[(_trace.feature == feature) & (_trace.n == n) & (_trace.metric == metric) & (_trace.interval == interval)]
    need(len(r) == 1, f"expected one trace row for {feature}/{n}/{metric}/{interval}")
    r = r.iloc[0]
    return f"{float(r.cov_uncond):.2f}\\pm{float(r.mc_se_uncond):.2f}"
_expect["TraceDurEssFive"] = _tcell("Flow Duration", 5000, "fpr", "ESS-Wilson")
_expect["TraceDurEssTwenty"] = _tcell("Flow Duration", 20000, "fpr", "ESS-Wilson")
_expect["TraceDurNaiveFive"] = _tcell("Flow Duration", 5000, "fpr", "naiveWilson")
_rc = pd.read_csv("results/recall_clock.csv")
def _rclock(n, clock):
    r = _rc[(_rc.n == n) & (_rc.clock == clock)]
    need(len(r) == 1, f"expected one recall-clock row for n={n} {clock}")
    return r.iloc[0]
for _n, _sn, _mn in ((5000, "RecallClockSubFive", "RecallClockMisFive"),
                     (20000, "RecallClockSubTwenty", "RecallClockMisTwenty")):
    _s, _mrow = _rclock(_n, "subsequence"), _rclock(_n, "missing")
    _expect[_sn] = f"{float(_s.cov_uncond):.2f}\\pm{float(_s.mc_se_uncond):.2f}"
    _expect[_mn] = f"{float(_mrow.cov_uncond):.2f}\\pm{float(_mrow.mc_se_uncond):.2f}"
    _gap = abs(float(_s.cov_uncond) - float(_mrow.cov_uncond))
    _tol = 2 * math.hypot(float(_s.mc_se_uncond), float(_mrow.mc_se_uncond))
    need(_gap <= _tol,
         f"recall clocks at n={_n} differ by {_gap:.3f}, above 2 combined SE {_tol:.3f}; "
         f"rewrite the closed-objection sentence before keeping it")
need("within two combined Monte Carlo standard errors" in body,
     "recall-clock closure sentence missing")

_metric = pd.read_csv("results/metric_level_intervals.csv")
def _mrow(dataset, detector, metric):
    r = _metric[(_metric.dataset == dataset) & (_metric.detector == detector) & (_metric.metric == metric)]
    need(len(r) == 1, f"expected one metric row for {dataset}/{detector}/{metric}")
    return r.iloc[0]
_mon = _mrow("CICIDS2017-Mon", "iforest", "fpr")
_wedf = _mrow("CICIDS2017-Wed", "iforest", "fpr")
_expect["MonIfFprRatio"] = f"{float(_mon.width_ratio):.2f}"
_expect["MonIfFprDif"] = f"{float(_mon.dif_geyer):.2f}"
_expect["WedIfFprDif"] = f"{float(_wedf.dif_geyer):.2f}"
_expect["FprNtwEss"] = _pm(_d20, "bg_ar__lab_campaign", "fpr", "corrWilson")
_expect["FprNtwNaive"] = _pm(_d20, "bg_ar__lab_campaign", "fpr", "naiveWilson")
_expect["FlowShuffleMed"] = f"{fm:.1f}"
_pairs = pd.read_csv("results/paired_block_comparisons.csv")
def _pair(statistic):
    r = _pairs[(_pairs.dataset == "CICIDS2017-Wed") & (_pairs.pair == "logreg-rf") & (_pairs.statistic == statistic)]
    need(len(r) == 1, f"expected the Wednesday logreg-rf {statistic} row")
    return r.iloc[0]
_flip = _pair("auc_diff")
_loss = _pair("loss_diff")
_expect["WedAucFlip"] = f"{float(_flip.estimate):.4f}"
need(bool(_flip.flip_iid_sig_mbb_not),
     "Wednesday logreg-rf AUC no longer flips; rewrite the ranking sentence")
need(bool(_loss.iid_excludes_0) and bool(_loss.mbb_excludes_0),
     "Wednesday logreg-rf loss difference no longer excludes zero on both arms; rewrite that sentence")


for _name, _val in _expect.items():
    need(f"\\newcommand{{\\{_name}}}{{{_val}}}" in macros,
         f"\\{_name} is not {_val} in prose_macros.tex")

# Every generated macro must be used: an unused one means the prose went back to a literal.
_defined = set(re.findall(r"\\newcommand\{\\(\w+)\}", macros))
_unused = sorted(t for t in _defined if "\\" + t not in body)
need(not _unused, f"prose macros defined but not used in the manuscript: {_unused}")

for _tok in ("MonIfFprRatio", "MonIfFprDif", "FprNtwEss", "RecallNtwEss", "AucNtwMbb",
             "FprLrdEss", "TraceDurEssFive", "TraceDurEssTwenty", "ResRate"):
    need("\\" + _tok in ab, f"abstract is missing \\{_tok}")
need("not a prevalence" in ab, "abstract prevalence caveat missing")
need(r"report $\neff$ and no interval" in ab, "abstract reporting-rule sentence missing")

def _expand_words(src):
    defs = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", macros))
    defs.update(dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                                open("paper/tables/corpus_macros.tex").read())))
    out = src
    for _ in range(4):
        out = re.sub(r"\\([A-Za-z]+)", lambda m: defs.get(m.group(1), " "), out)
    out = out.replace("~", " ")
    out = re.sub(r"[{}$\\]", " ", out)
    return [w for w in re.split(r"\s+", out) if re.search(r"[A-Za-z0-9]", w)]
_wc = len(_expand_words(ab))
need(150 <= _wc <= 200,
     f"abstract is {_wc} words; Elsevier research-article abstracts run to about 200, "
     f"and an abstract this dense is already at the limit of what a reader will parse")

def _render_item(item):
    s = item.strip().replace("\\neff", "n_eff").replace("\\MonIfFprRatio", _expect["MonIfFprRatio"])
    s = s.replace("$", "").replace("{", "").replace("}", "")
    s = re.sub(r"\\[A-Za-z]+", "", s)
    return re.sub(r"\s+", " ", s).strip()
_h = re.search(r"\\begin\{highlights\}(.*)\\end\{highlights\}", body, re.S)
need(_h is not None, "highlights environment missing")
_items = [_render_item(x) for x in re.findall(r"\\item\s+(.*)", _h.group(1))]
need(3 <= len(_items) <= 5, f"expected 3 to 5 highlights, got {len(_items)}")
for _item in _items:
    need(len(_item) <= 85, f"highlight exceeds 85 characters ({len(_item)}): {_item}")
_htxt = [ln.strip() for ln in open("paper/highlights.txt") if ln.strip()]
need(_htxt == _items, f"highlights.txt does not match the manuscript highlights: {_items}")

_kw = re.search(r"\\textbf\{Keywords\.\}\\enspace(.*?)\\vspace", body, re.S)
need(_kw is not None, "keywords block not found in the manuscript")
_kwm = re.sub(r"[%\s]+", " ", _kw.group(1)).strip().rstrip(".")
_kwf = open("paper/keywords.txt").read().strip().rstrip(".")
need(_kwm == _kwf, f"keywords.txt does not match the manuscript:\n  tex: {_kwm!r}\n  txt: {_kwf!r}")

_readme = open("README.md").read()
need(_expect["FlowQualMed"] in _readme and _expect["WinQMed"] in _readme,
     "README is missing the qualifying flow and window medians")
need("17.3" not in _readme, "README still quotes the pre-QC flow median 17.3")

print(f"abstract-check OK: packet qual~{pk_q:.1f}/range~{pk_rng_hi:.0f}, flow~{fm:.0f}, "
      f"window qual~{win_q:.1f}/all~{win_all:.0f} -- all match dif_headline.csv")
