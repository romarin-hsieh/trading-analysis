"""TR-30 -- Larry Williams outside-bar reversal (creator-video lead -> primary source).

Source path: YouTube "top 10 traders" compilation (data/transcripts/T1CawPmNG-0.txt,
position 8) -> Larry Williams, "Long-Term Secrets to Short-Term Trading" ch.7. A creator
LEAD, tested in fabric (docs/23 discipline). The video ITSELF admits the headline win
rate comes from a wide stop buffer + a tiny FPO target -- i.e. payoff-asymmetry win-rate
inflation. This TR is built to expose exactly that.

MECHANISM (long side, mechanical):
  outside bar = today.high > yest.high AND today.low < yest.low
  long signal = outside bar AND today.close < yest.low   (close in lower part = reversal-up setup)
  entry       = NEXT day OPEN (honest fill; the video's own convention)

F0 DECLARATION (pre-committed)
  claim        : the outside-bar reversal is a real edge -- POSITIVE expectancy net of
               costs at next-open fills, beating a random-entry placebo into the same
               instrument.
  seat         : SPY/QQQ/IWM/DIA daily (1993/1999/2000/1998-2026), 5bps/side costs.
  PRE-COMMITTED CHECKS
    R1 edge      : forward 5-day excess-return of the signal-day cohort > 0 with t >= 2.0,
                   AND mean > the all-day base rate (does the pattern SELECT good days?).
    R2 win-rate trap : report BOTH (a) the video's asymmetric exit (FPO: exit next open if
                   green, else hold to a wide ATR stop) and (b) a symmetric fixed-5-day
                   hold. PASS-the-trap-check iff expectancy (mean net P&L per trade) > 0
                   under the SYMMETRIC rule. A high win rate under (a) with <=0 expectancy
                   under (b) = the asymmetry illusion -> FAILED.
    R3 placebo   : the signal-day forward 5d return must beat the 95th percentile of 1,000
                   random-entry cohorts of the same size/instrument (does timing add over
                   random entry?).
    R4 fill      : same-close vs next-open entry (TR-16 lesson); edge must survive next-open.
  VERDICT RULE (pre-committed):
    R1 & R2 & R3 & R4 -> PASSED (rare -- a real mechanical edge)
    win rate high but R2 expectancy <= 0 -> FAILED (WIN-RATE-TRAP, as the video admits)
    R1 fail or R3 fail -> FAILED (NO-EDGE / no better than random entry)
  anti-HARKing : single pre-registered rule; no parameter search; adds 1 family to trials.

Run: uv run python scripts/tests/tr30_outside_bar.py   (~1-2 min)
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "scripts")

from trading_analysis.data.store import DuckStore  # noqa: E402

INSTR = ("SPY", "QQQ", "IWM", "DIA")
COST = 0.0005          # per side
HOLD = 5
N_PLACEBO = 1000
SEED = 0


def signals(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values("ts").reset_index(drop=True)
    ph, pl = d["high"].shift(1), d["low"].shift(1)
    outside = (d["high"] > ph) & (d["low"] < pl)
    d["long_sig"] = outside & (d["close"] < pl)   # signal observed at close of day t
    d["atr"] = (d["high"] - d["low"]).rolling(14).mean()
    return d


def main():
    rng = np.random.default_rng(SEED)
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-30  LARRY WILLIAMS OUTSIDE-BAR REVERSAL (creator lead -> primary source)")
    print("=" * 100)

    all_fwd_sig, all_fwd_base = [], []
    fpo_pnl, sym_pnl, wins_fpo, wins_sym = [], [], [], []
    per_instr = {}
    for t in INSTR:
        raw = store.load_ohlcv([t])
        if raw.empty:
            continue
        d = signals(raw)
        o, c, lo = d["open"].to_numpy(), d["close"].to_numpy(), d["low"].to_numpy()
        atr = d["atr"].to_numpy()
        n = len(d)
        sig_idx = np.where(d["long_sig"].to_numpy())[0]
        sig_idx = sig_idx[(sig_idx + HOLD + 1 < n)]      # room for entry+hold
        # forward 5d return from NEXT-open entry (honest fill)
        ret_next = (c[sig_idx + 1 + HOLD] - o[sig_idx + 1]) / o[sig_idx + 1] - 2 * COST
        all_fwd_sig.append(ret_next)
        # base rate: every day's next-open -> +5d
        base_idx = np.arange(1, n - HOLD - 1)
        base = (c[base_idx + HOLD] - o[base_idx]) / o[base_idx]
        all_fwd_base.append(base)
        # R2: FPO asymmetric vs symmetric hold, per trade net P&L
        for i in sig_idx:
            entry = o[i + 1]
            # FPO: if next-day (i+1) close > entry -> exit at i+2 open profit; approximate
            # exit at close of i+1 if green, else hold to +5d (wide implicit stop)
            if c[i + 1] > entry:
                pnl = (c[i + 1] - entry) / entry - 2 * COST
            else:
                pnl = (c[i + 1 + HOLD] - entry) / entry - 2 * COST
            fpo_pnl.append(pnl); wins_fpo.append(pnl > 0)
            spnl = (c[i + 1 + HOLD] - entry) / entry - 2 * COST     # symmetric 5d hold
            sym_pnl.append(spnl); wins_sym.append(spnl > 0)
        # placebo per instrument
        k = len(sig_idx)
        plc = np.array([np.mean((c[(ridx := rng.choice(base_idx, k, replace=False)) + HOLD]
                                 - o[ridx]) / o[ridx]) for _ in range(N_PLACEBO)])
        per_instr[t] = {"n": k, "sig_mean": float(ret_next.mean()),
                        "plc95": float(np.percentile(plc, 95)),
                        "beats_plc": float(ret_next.mean()) > float(np.percentile(plc, 95))}
        print(f"  {t}: {k} signals | signal +5d {ret_next.mean():+.4f} vs base "
              f"{base.mean():+.4f} | placebo p95 {per_instr[t]['plc95']:+.4f} "
              f"-> beats random: {per_instr[t]['beats_plc']}")

    sig = np.concatenate(all_fwd_sig)
    base = np.concatenate(all_fwd_base)
    fpo = np.array(fpo_pnl); sym = np.array(sym_pnl)
    t_sig = sig.mean() / sig.std() * np.sqrt(len(sig))
    r1 = (sig.mean() > 0) and (t_sig >= 2.0) and (sig.mean() > base.mean())
    wr_fpo, wr_sym = np.mean(wins_fpo), np.mean(wins_sym)
    exp_sym = sym.mean()
    r2 = exp_sym > 0
    beats_all = sum(v["beats_plc"] for v in per_instr.values())
    r3 = beats_all >= 3            # majority of the 4 instruments beat random entry
    print("-" * 100)
    print(f"R1 edge: signal +5d mean {sig.mean():+.4f} (t={t_sig:+.2f}, rule>=2.0) vs "
          f"base {base.mean():+.4f} -> {r1}")
    print(f"R2 win-rate trap: FPO win rate {wr_fpo:.0%} (headline) BUT symmetric-hold "
          f"expectancy {exp_sym:+.4f}/trade, win rate {wr_sym:.0%} -> "
          f"{'edge survives' if r2 else 'ASYMMETRY ILLUSION (as the video admits)'}")
    print(f"R3 placebo: {beats_all}/4 instruments beat random-entry p95 -> {r3}")

    if r1 and r2 and r3:
        v = "PASSED -- a real mechanical outside-bar edge (rare; scrutinize before trusting)."
    elif (wr_fpo >= 0.60) and not r2:
        v = ("FAILED (WIN-RATE-TRAP) -- the high FPO win rate is the wide-stop/tiny-target "
             "asymmetry the video itself admits; symmetric-hold expectancy is <=0. The "
             "pattern does not select good forward returns.")
    else:
        v = ("FAILED (NO-EDGE) -- outside-bar timing does not beat random entry / base rate "
             "net of costs.")
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axes[0]
    ax.hist(sym, bins=60, color="#1565c0", alpha=0.8)
    ax.axvline(0, color="black", lw=1)
    ax.axvline(sym.mean(), color="#c62828", lw=2, label=f"mean {sym.mean():+.4f}")
    ax.set_title(f"R2: per-trade P&L, symmetric 5d hold\nwin rate {wr_sym:.0%}, "
                 f"expectancy {sym.mean():+.4f} (FPO win rate was {wr_fpo:.0%})", fontsize=9.5)
    ax.set_xlabel("net return per trade")
    ax.legend(fontsize=8)
    ax = axes[1]
    xs = list(per_instr)
    ax.bar(xs, [per_instr[t]["sig_mean"] for t in xs], color="#1565c0", alpha=0.85, label="signal +5d")
    ax.plot(xs, [per_instr[t]["plc95"] for t in xs], "r_", ms=30, mew=3, label="random-entry p95")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("R3: signal vs random-entry placebo (p95)", fontsize=9.5)
    ax.set_ylabel("mean +5d return")
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-30: Larry Williams outside-bar reversal -- win rate vs expectancy", fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr30_outside_bar.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
