"""Hostile audit of the three interval constructions. Not a paper table; a mechanism check.

A. Is the ESS variance identity exact, or an approximation? For a stationary binary series the
   long-run variance is gamma_0 * tau_int = p(1-p) * tau_int by definition of tau_int, so the
   substitution is exact at the population level. What is estimated, and can be wrong, is tau.
   Measure the bias of tau-hat on the rare alarm indicator against a long-run value.
B. Does each plug-in deliver the right WIDTH? Compare the mean reported standard error (or half
   width) against the Monte Carlo standard deviation of the estimator itself. A ratio below 1
   means the interval is too narrow and undercoverage is a variance failure, not a shape failure.
C. Is the attack-row subsequence stationary in its own index? It is a concatenation of
   within-campaign runs joined at campaign boundaries. Compare tau on the concatenated
   subsequence against tau within single campaigns.
D. Computability: what drives the non-computable replicates, and does it persist at n=20000?
"""
import sys
sys.path.insert(0, "src")
import numpy as np
from scipy import stats as st
from t13.sim import generate, SCENARIOS
from t13.dif import integrated_autocorrelation_time
from t13 import ci as C

FPR = 0.01
BOTH = SCENARIOS["bg_ar__lab_campaign"]


def tau_of(x):
    try:
        return integrated_autocorrelation_time(np.asarray(x, float))[0]
    except Exception:
        return np.nan


def section(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# ---------------- A: tau-hat bias on the rare alarm indicator ----------------
section("A. tau-hat on the benign alarm indicator: short series vs long-run value")
rng = np.random.default_rng(11)
a, s = generate(2_000_000, rng=rng, **BOTH)
thr = float(np.quantile(s[a == 0], 1 - FPR))
long_alarms = (s[a == 0] > thr).astype(float)
tau_long = tau_of(long_alarms)
tau_score_long = tau_of(s[a == 0][:200_000])
print(f"long-run alarm-indicator tau (n={long_alarms.size}): {tau_long:.3f}")
print(f"long-run benign-score tau (n=200000):                {tau_score_long:.3f}")
print("the alarm indicator is a thresholded score: its tau is much smaller than the score's")

for n in (5000, 20000):
    taus = []
    rng = np.random.default_rng(5)
    for _ in range(300):
        a, s = generate(2 * n, rng=rng, **BOTH)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < 30 or (a_te == 0).sum() < 30:
            continue
        t = float(np.quantile(s_tr[a_tr == 0], 1 - FPR))
        taus.append(tau_of((s_te[a_te == 0] > t).astype(float)))
    taus = np.array([x for x in taus if x == x])
    print(f"n={n:5d}: tau-hat mean {taus.mean():.3f}  median {np.median(taus):.3f}  "
          f"sd {taus.std():.3f}  frac floored at 1.0 {np.mean(taus <= 1.0 + 1e-9):.3f}  "
          f"relative bias vs long-run {taus.mean()/tau_long - 1:+.3f}")

# ---------------- B: width check, FPR and recall ----------------
section("B. reported width vs true sampling variability")
z = st.norm.ppf(0.975)
for n in (5000, 20000):
    rng = np.random.default_rng(23)
    phat, wilson_half, ess_half, naive_half = [], [], [], []
    rhat, r_ess_se, r_naive_se, r_tau = [], [], [], []
    for _ in range(400):
        a, s = generate(2 * n, rng=rng, **BOTH)
        a_tr, s_tr, a_te, s_te = a[:n], s[:n], a[n:], s[n:]
        if (a_tr == 0).sum() < 30 or (a_te == 0).sum() < 30 or a_te.sum() < 30:
            continue
        thr = float(np.quantile(s_tr[a_tr == 0], 1 - FPR))
        alarms = (s_te[a_te == 0] > thr).astype(float)
        hits = (s_te[a_te == 1] > thr).astype(float)
        phat.append(alarms.mean())
        try:
            _, lo, hi, _ = C.wilson_ess_ci(alarms)
            wilson_half.append((hi - lo) / 2)
        except Exception:
            pass
        _, lo, hi = C.wilson(alarms.sum(), alarms.size)[0], *C.wilson(alarms.sum(), alarms.size)[1:]
        naive_half.append((hi - lo) / 2)
        rhat.append(hits.mean())
        try:
            _, lo, hi, neff = C.ess_plugin_ci(hits)
            r_ess_se.append((hi - lo) / 2 / z)
            r_tau.append(hits.size / neff)
        except Exception:
            pass
        r_naive_se.append(hits.std(ddof=1) / np.sqrt(hits.size))
    phat = np.array(phat); rhat = np.array(rhat)
    print(f"\n n={n}, reps={phat.size}")
    print(f"  FPR    true sd of p-hat            {phat.std(ddof=1):.5f}")
    print(f"         mean ESS-Wilson half width  {np.mean(wilson_half):.5f}  "
          f"implied se {np.mean(wilson_half)/z:.5f}  ratio to true sd {np.mean(wilson_half)/z/phat.std(ddof=1):.3f}")
    print(f"         mean naive Wilson half width{np.mean(naive_half):.5f}  "
          f"ratio {np.mean(naive_half)/z/phat.std(ddof=1):.3f}")
    print(f"  recall true sd of recall-hat       {rhat.std(ddof=1):.5f}")
    print(f"         mean ESS plug-in se         {np.mean(r_ess_se):.5f}  "
          f"ratio {np.mean(r_ess_se)/rhat.std(ddof=1):.3f}   mean tau of subsequence {np.mean(r_tau):.2f}")
    print(f"         mean naive se               {np.mean(r_naive_se):.5f}  "
          f"ratio {np.mean(r_naive_se)/rhat.std(ddof=1):.3f}")

# ---------------- C: is the attack subsequence stationary in its own index? ----------------
section("C. attack-row subsequence: concatenated vs within-campaign dependence")
rng = np.random.default_rng(31)
conc, within, ncamp, camplen = [], [], [], []
for _ in range(60):
    a, s = generate(40_000, rng=rng, **BOTH)
    thr = float(np.quantile(s[a == 0], 1 - FPR))
    hits = (s[a == 1] > thr).astype(float)
    if hits.size < 200:
        continue
    conc.append(tau_of(hits))
    # split the attack rows back into campaigns
    idx = np.flatnonzero(a == 1)
    brk = np.flatnonzero(np.diff(idx) > 1) + 1
    runs = np.split(np.arange(idx.size), brk)
    runs = [r for r in runs if r.size >= 60]
    ncamp.append(len(np.split(idx, brk)))
    camplen.append(np.mean([r.size for r in np.split(idx, brk)]))
    if runs:
        within.append(np.nanmean([tau_of(hits[r]) for r in runs]))
print(f"replicates {len(conc)}  mean campaigns per draw {np.mean(ncamp):.1f}  "
      f"mean campaign length {np.mean(camplen):.1f}")
print(f"tau of the concatenated attack subsequence : {np.nanmean(conc):.3f}")
print(f"mean tau within single campaigns (>=60 rows): {np.nanmean(within):.3f}")
print("if these differ, the subsequence is not stationary in its own index; the plug-in tau is a")
print("mixture of within-campaign dependence and the near-independent campaign joins")

# ---------------- D: computability ----------------
section("D. what makes an AUC/recall replicate non-computable")
for n in (5000, 20000):
    rng = np.random.default_rng(43)
    natt = []
    for _ in range(500):
        a, _ = generate(2 * n, rng=rng, **BOTH)
        natt.append(int(a[n:].sum()))
    natt = np.array(natt)
    print(f"n={n:5d}: P(no attack rows in test half) {np.mean(natt == 0):.3f}  "
          f"P(<2) {np.mean(natt < 2):.3f}  P(<3) {np.mean(natt < 3):.3f}  "
          f"median attacks {np.median(natt):.0f}  mean {natt.mean():.0f}")
