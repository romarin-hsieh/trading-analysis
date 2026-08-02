"""TR-43 -- L3 EVT tail module vs the incumbent (risk-engine v2, second challenger).

TR-42 killed L2: moving exposure on a regime signal is timing, and timing has now lost
eight times. What is left in the risk engine are ESTIMATION-QUALITY problems, which the
iron law does not govern -- you are not deciding WHEN to be exposed, you are deciding
how much loss to budget for. This is the first of those.

Incumbent: TR-04b's Student-t tail on the flagship's return stream, used to size the
drawdown budget (the L-scale). Challenger: McNeil-Frey style conditional EVT -- fit a
Generalized Pareto to the exceedances over a high threshold of DEVOLATILIZED residuals
(EWMA vol), then re-inflate. The question is narrow and testable: which model predicts
the loss distribution better out of sample?

F0 DECLARATION (pre-committed)
  claim  : conditional EVT predicts the flagship's tail (VaR/CVaR at 99% and 99.5%)
         better out of sample than the incumbent Student-t and than the empirical
         (historical-simulation) baseline.
  seat   : flagship daily returns 2015-2026 (build_combo) AND the 50-year monthly analog
         (TR-35 engine) for a regime-diverse second look. Expanding-window, one-step-
         ahead, 500-day (analog: 120-month) burn-in -- no in-sample tail fitting.
  models : (1) Student-t (incumbent, TR-04b), (2) empirical HS, (3) EVT-GPD on EWMA-
         devolatilized residuals, threshold = 10% tail, MLE fit.
  CAL    : incumbent Student-t must reproduce TR-04b's qualitative finding on this
         stream -- normal VaR is rejected by Kupiec at 99% while Student-t is not.
         Fail -> STOP (stream/machinery drift).
  C1 (decisive): Kupiec unconditional-coverage LR + Christoffersen independence test on
         99% and 99.5% VaR breaches. ADOPT requires EVT to be non-rejected where a rival
         is rejected, or strictly closer breach rates at BOTH levels.
  C2     : CVaR accuracy -- mean realized loss beyond VaR vs predicted, RMSE across the
         two levels (a VaR test alone cannot see tail SHAPE).
  C3     : the decision that actually consumes this -- the L-scale. Max leverage whose
         predicted 99% one-day loss stays inside a 20% drawdown budget, per model. If
         all three give the same L, the challenger is academically better and
         operationally irrelevant, and the write-up must say so.
  C4     : analog seat 1975-2026 (monthly) as the regime-diverse replication.
  anti-HARKing : threshold 10% and both VaR levels fixed here before running; no
         threshold search; trials +1 (same risk-engine family as TR-42).

Run: uv run python scripts/tests/tr43_evt_tail.py   (~4 min)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
sys.path.insert(0, "scripts/tests")

plt.rcParams["font.family"] = ["Microsoft JhengHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

LEVELS = (0.99, 0.995)
TAIL_FRAC = 0.10
LAMBDA = 0.94
BURN_D, BURN_M = 500, 120
DD_BUDGET = 0.20


def ewma_vol(x: np.ndarray, lam: float = LAMBDA) -> float:
    w = lam ** np.arange(len(x))[::-1]
    w /= w.sum()
    return float(np.sqrt((w * (x - x.mean()) ** 2).sum()))


def var_student_t(x: np.ndarray, q: float) -> tuple[float, float]:
    df, loc, sc = stats.t.fit(x)
    v = float(stats.t.ppf(1 - q, df, loc, sc))
    # CVaR for student-t
    xs = stats.t.rvs(df, loc, sc, size=20000, random_state=0)
    c = float(xs[xs <= v].mean()) if (xs <= v).any() else v
    return v, c


def var_hs(x: np.ndarray, q: float) -> tuple[float, float]:
    v = float(np.quantile(x, 1 - q))
    tail = x[x <= v]
    return v, float(tail.mean()) if len(tail) else v


def var_evt(x: np.ndarray, q: float) -> tuple[float, float]:
    """Conditional EVT: devolatilize with EWMA, fit GPD to lower-tail exceedances."""
    s = ewma_vol(x)
    if s <= 0:
        return var_hs(x, q)
    z = x / s
    u = np.quantile(z, TAIL_FRAC)                 # negative threshold
    exc = u - z[z < u]                            # positive exceedances below u
    if len(exc) < 20:
        return var_hs(x, q)
    try:
        c, _loc, scale = stats.genpareto.fit(exc, floc=0)
    except Exception:
        return var_hs(x, q)
    nu, n = len(exc), len(z)
    p = 1 - q
    if c == 0:
        zq = u - scale * np.log(p * n / nu)
    else:
        zq = u - (scale / c) * ((p * n / nu) ** (-c) - 1)
    v = float(zq * s)
    # GPD CVaR (mean excess beyond VaR), guarding c >= 1 (infinite mean)
    if c < 1:
        cv = float((zq - (scale + c * (u - zq)) / (1 - c)) * s)
    else:
        cv = v * 1.5
    return v, cv


MODELS = {"Student-t(現役)": var_student_t, "歷史模擬": var_hs, "EVT-GPD(挑戰者)": var_evt}


def kupiec(breaches: np.ndarray, q: float) -> float:
    n, x = len(breaches), int(breaches.sum())
    p = 1 - q
    if x == 0:
        return 1.0
    ph = x / n
    lr = -2 * ((n - x) * np.log(1 - p) + x * np.log(p)
               - (n - x) * np.log(1 - ph) - x * np.log(ph))
    return float(1 - stats.chi2.cdf(lr, 1))


def christoffersen(b: np.ndarray) -> float:
    """Independence of breaches (clustering test)."""
    b = b.astype(int)
    n00 = n01 = n10 = n11 = 0
    for i in range(1, len(b)):
        if b[i - 1] == 0 and b[i] == 0:
            n00 += 1
        elif b[i - 1] == 0 and b[i] == 1:
            n01 += 1
        elif b[i - 1] == 1 and b[i] == 0:
            n10 += 1
        else:
            n11 += 1
    if (n01 + n11) == 0 or (n00 + n01) == 0 or (n10 + n11) == 0:
        return 1.0
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    if p01 in (0, 1) or p11 in (0, 1) or p in (0, 1):
        return 1.0
    lr = -2 * ((n00 + n10) * np.log(1 - p) + (n01 + n11) * np.log(p)
               - n00 * np.log(1 - p01) - n01 * np.log(p01)
               - n10 * np.log(1 - p11) - n11 * np.log(p11))
    return float(1 - stats.chi2.cdf(lr, 1))


def backtest(r: pd.Series, burn: int) -> dict:
    x = r.to_numpy()
    out = {m: {q: {"br": [], "loss_beyond": [], "cvar_pred": []} for q in LEVELS}
           for m in MODELS}
    for t in range(burn, len(x)):
        hist = x[:t]
        for m, fn in MODELS.items():
            for q in LEVELS:
                v, c = fn(hist, q)
                brk = x[t] < v
                out[m][q]["br"].append(brk)
                if brk:
                    out[m][q]["loss_beyond"].append(x[t])
                    out[m][q]["cvar_pred"].append(c)
    return out


def report(res: dict, label: str, n_obs: int) -> dict:
    print(f"\n{label}(樣本外 {n_obs} 期):")
    summary = {}
    for m in MODELS:
        cells = []
        for q in LEVELS:
            b = np.array(res[m][q]["br"])
            rate = b.mean()
            pk = kupiec(b, q)
            pc = christoffersen(b)
            lb = np.array(res[m][q]["loss_beyond"])
            cp = np.array(res[m][q]["cvar_pred"])
            cerr = float(np.sqrt(np.mean((lb - cp) ** 2))) if len(lb) else np.nan
            cells.append((q, rate, pk, pc, cerr))
        summary[m] = cells
        s = " | ".join(f"{q:.1%}: 破線 {rate:.2%}(期望 {1-q:.1%})"
                       f" Kupiec p={pk:.3f}{'*' if pk < 0.05 else ''}"
                       f" 獨立性 p={pc:.3f} CVaR-RMSE {cerr*1e4:.0f}bps"
                       for q, rate, pk, pc, cerr in cells)
        print(f"  {m:<18}: {s}")
    return summary


def main():
    import validate_recommendation as vr
    rp, _e, _s = vr.build_combo()
    print("=" * 104)
    print("TR-43  L3 EVT 尾部模組 vs 現役 Student-t(風險引擎 v2 第二挑戰者)")
    print("=" * 104)

    res_d = backtest(rp, BURN_D)
    n_d = len(rp) - BURN_D

    # CAL: normal VaR must be rejected at 99% where Student-t is not (TR-04b finding)
    x = rp.to_numpy()
    br_norm = []
    for t in range(BURN_D, len(x)):
        h = x[:t]
        v = float(stats.norm.ppf(0.01, h.mean(), h.std(ddof=1)))
        br_norm.append(x[t] < v)
    p_norm = kupiec(np.array(br_norm), 0.99)
    p_t = kupiec(np.array(res_d["Student-t(現役)"][0.99]["br"]), 0.99)
    cal = p_norm < 0.05 <= p_t
    print(f"CAL(重現 TR-04b):常態 VaR 99% Kupiec p={p_norm:.4f}(應 <0.05)、"
          f"Student-t p={p_t:.3f}(應 ≥0.05) -> {'PASS' if cal else 'FAIL'}")
    if not cal:
        print("VERDICT: INVALID-TEST -- stream/machinery drift vs TR-04b.")
        return

    s_live = report(res_d, "C1/C2 實際座位 2015-2026(日頻)", n_d)

    # ---- C3 the decision this feeds: the L-scale ----
    print("\nC3 這個模組真正餵養的決策(L 刻度上限;20% 回撤預算、99% 單日損失):")
    ls = {}
    for m, fn in MODELS.items():
        v, _ = fn(rp.to_numpy(), 0.99)
        ls[m] = DD_BUDGET / abs(v) / 100 if v < 0 else np.nan
        print(f"  {m:<18}: 單日 99% 損失 {v*100:.2f}% → 允許 L ≈ {DD_BUDGET/abs(v)/100:.2f}"
              f"(以 20% 預算 / 100 倍單日換算)")
    same_L = (max(ls.values()) - min(ls.values())) < 0.15

    # ---- C4 analog seat ----
    import tr42_correlation_brake as t42
    sleeves, w, _mkt = t42.build_analog()
    sl = sleeves.loc["1975-01":]
    w = w.loc["1975-01":]
    analog = (w * sl).sum(axis=1).where(w.notna().all(axis=1)).dropna()
    res_a = backtest(analog, BURN_M)
    s_ana = report(res_a, "C4 類比座位 1975-2026(月頻,regime 多樣)", len(analog) - BURN_M)

    # ---- verdict ----
    def rejected(sm, m):
        return sum(1 for q, rate, pk, pc, ce in sm[m] if pk < 0.05)

    evt_rej = rejected(s_live, "EVT-GPD(挑戰者)") + rejected(s_ana, "EVT-GPD(挑戰者)")
    inc_rej = rejected(s_live, "Student-t(現役)") + rejected(s_ana, "Student-t(現役)")
    evt_cvar = np.nanmean([c[4] for c in s_live["EVT-GPD(挑戰者)"]]
                          + [c[4] for c in s_ana["EVT-GPD(挑戰者)"]])
    inc_cvar = np.nanmean([c[4] for c in s_live["Student-t(現役)"]]
                          + [c[4] for c in s_ana["Student-t(現役)"]])
    better = (evt_rej < inc_rej) or (evt_rej == inc_rej and evt_cvar < inc_cvar)
    if better and not same_L:
        v = "ADOPT -- EVT 尾部較準且改變 L 刻度決策。"
    elif better:
        v = ("BETTER-BUT-INERT -- EVT 在統計上較準,但三個模型給出的 L 刻度幾乎相同"
             f"(差 {max(ls.values())-min(ls.values()):.2f}):學術上贏、操作上無差別,不入列。")
    else:
        v = "REJECTED -- EVT 未優於現役 Student-t;現役維持。"
    print("-" * 104)
    print(f"VERDICT: {v}")
    print(f"(拒絕次數 EVT {evt_rej} vs 現役 {inc_rej};CVaR-RMSE {evt_cvar*1e4:.0f} vs "
          f"{inc_cvar*1e4:.0f} bps)")
    print("=" * 104)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.6))
    ax = axes[0]
    xs = np.arange(len(MODELS))
    for i, q in enumerate(LEVELS):
        rates = [s_live[m][i][1] * 100 for m in MODELS]
        ax.bar(xs + (i - 0.5) * 0.35, rates, 0.35, label=f"{q:.1%} VaR",
               color=["#1565c0", "#f9a825"][i], alpha=0.9)
        ax.axhline((1 - q) * 100, color=["#1565c0", "#f9a825"][i], ls="--", lw=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(list(MODELS), fontsize=9)
    ax.set_ylabel("實際破線率 (%)")
    ax.set_title("C1:破線率 vs 名目(虛線=期望)", fontsize=10.5)
    ax.legend(fontsize=9)
    ax = axes[1]
    cv_live = [np.nanmean([c[4] for c in s_live[m]]) * 1e4 for m in MODELS]
    cv_ana = [np.nanmean([c[4] for c in s_ana[m]]) * 1e4 for m in MODELS]
    ax.bar(xs - 0.2, cv_live, 0.4, label="實際座位(日)", color="#1565c0", alpha=0.9)
    ax.bar(xs + 0.2, cv_ana, 0.4, label="類比座位(月)", color="#2e7d32", alpha=0.9)
    ax.set_xticks(xs)
    ax.set_xticklabels(list(MODELS), fontsize=9)
    ax.set_ylabel("CVaR 預測誤差 RMSE (bps)")
    ax.set_title("C2:尾部形狀準不準", fontsize=10.5)
    ax.legend(fontsize=9)
    for a in axes:
        a.grid(alpha=0.3, axis="y")
    fig.suptitle("TR-43:EVT 尾部模組 —— 估計品質問題(不受擇時鐵律管轄)", fontsize=12.5)
    fig.tight_layout()
    outp = Path("docs/tests/img/tr43_evt_tail.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
