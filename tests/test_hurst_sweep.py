"""The long-memory sweep must be the reported experiment with H moved, and nothing else."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")

from t13.sim import SCENARIOS, coverage_run  # noqa: E402


def test_sweep_varies_only_H():
    """The script builds its scenarios as dict(SCENARIOS['lrd_H0.8'], H=...). Every other
    generator parameter must therefore be identical to the reported cell."""
    base = SCENARIOS["lrd_H0.8"]
    for H in (0.55, 0.6, 0.7, 0.9):
        kw = dict(base, H=H)
        assert kw["H"] == H
        assert {k: v for k, v in kw.items() if k != "H"} == {k: v for k, v in base.items() if k != "H"}


def test_H08_arm_reproduces_the_frozen_cell():
    """Same seed, n, R, B and scenario kwargs -> identical coverage, not merely close.
    R is small here; the point is determinism of the path, not the coverage value."""
    kw = dict(SCENARIOS["lrd_H0.8"])
    a, _ = coverage_run("a", kw, n=400, R=6, B=20, seed=7)
    b, _ = coverage_run("b", dict(kw, H=0.8), n=400, R=6, B=20, seed=7)
    key = ["metric", "interval"]
    a = a.sort_values(key).reset_index(drop=True)
    b = b.sort_values(key).reset_index(drop=True)
    assert a.cov_uncond.tolist() == b.cov_uncond.tolist()


def test_committed_sweep_matches_the_committed_coverage_run():
    """results/hurst_sweep.csv H=0.8 must equal results/coverage_sim.csv lrd_H0.8."""
    hs = pd.read_csv("results/hurst_sweep.csv")
    cs = pd.read_csv("results/coverage_sim.csv")
    h8 = hs[hs.H.round(2) == 0.80]
    ref = cs[cs.scenario == "lrd_H0.8"]
    assert len(h8) and len(ref)
    merged = h8.merge(ref, on=["metric", "interval"], suffixes=("_sweep", "_ref"))
    assert len(merged) == len(ref)
    assert merged.cov_uncond_sweep.tolist() == merged.cov_uncond_ref.tolist()


def test_committed_sweep_is_monotone_in_H():
    """The manuscript states the degradation is monotone; if a rerun breaks that, the prose
    is wrong and this test is the first thing to fail."""
    hs = pd.read_csv("results/hurst_sweep.csv")
    fpr = hs[(hs.metric == "fpr") & (hs.interval == "corrWilson")].sort_values("H")
    assert np.all(np.diff(fpr.cov_uncond.to_numpy()) <= 0)
    meta = pd.read_csv("results/hurst_sweep_meta.csv").sort_values("H")
    assert np.all(np.diff(meta.mean_neff_score.to_numpy()) <= 0)


def test_gate_orderings_the_paper_depends_on():
    """The recommendation is that the agreement gate be read on the score series. That rests on
    two orderings holding across the grid: the alarm gate is uniformly more permissive, and the
    score gate falls as H rises."""
    gt = pd.read_csv("diagnostics/p127_gate.csv")
    alarm = gt[gt.series == "alarm"].sort_values("H").gate_pass_rate.to_numpy()
    score = gt[gt.series == "score"].sort_values("H").gate_pass_rate.to_numpy()
    assert np.all(alarm >= score)
    assert np.all(np.diff(score) <= 0)
    assert score[-1] <= 0.25 <= alarm[-1]


def test_gate_is_the_prespecified_rule():
    """p127 must apply the rule the paper states: agreement within 2x AND n_eff >= 50."""
    sys.path.insert(0, "diagnostics")
    from p127_gate_vs_memory import AGREE_FACTOR, NEFF_FLOOR, gate

    assert AGREE_FACTOR == 2.0 and NEFF_FLOOR == 50
    rng = np.random.default_rng(0)
    passes, agrees, neff_ok, tg, tb, neff = gate(rng.normal(size=4000))
    assert passes and agrees and neff_ok and neff > 50
    short = np.array([1.0, 0.0] * 20)          # n_eff far below the floor
    assert not gate(short)[0]
