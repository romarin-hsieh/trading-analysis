"""TR-30b -- Larry Williams outside bar, FAITHFUL engine (machine-fidelity redo of TR-30).

Reopen basis: USER AUDIT (2026-07-12). TR-30 was found unfaithful to its source on
four counts, verified against the transcript (data/transcripts/T1CawPmNG-0.txt):
  1. the >=2x body filter (video default minRatio=2) was in the F0 plan but ABSENT
     from the code -- a real implementation bug;
  2. no stop was implemented (video primary: outside-bar low - 0.2*ATR(14) buffer);
  3. FPO was approximated as a single next-CLOSE check (video: check EVERY day's OPEN,
     exit at the first profitable open);
  4. the placebo compared raw 5-day returns instead of sharing the exit engine.
This is the T1 machine-fidelity rule (TR-17b lesson) applied to creator videos:
re-test only after the machine reproduces the source's claim.

F0 DECLARATION (pre-committed)
  claim (video) : with the faithful engine (2x body filter, PHL+0.2*ATR stop, FPO
                exit) the win rate is "extraordinarily high", admittedly via payoff
                asymmetry; the open question TR-30 was meant to answer: does the
                outside-bar ENTRY add value over random entry, exits held equal?
  seat          : SPY/QQQ/IWM/DIA daily (real traded opens), 5bps/side.
                Era split on SPY: 1993-1998 (book in-sample tail) vs 1999-2026
                (post-publication). 1982-1992 requires paid futures data (info cost).
  ENGINE (single faithful config, video defaults -- no parameter search):
                signal day i: outside bar (hi>prev hi, lo<prev lo) AND close<prev low
                AND body >= 2x prev body. Enter open of i+1. Stop = low[i]-0.2*ATR14[i]
                (gap-through exits at the open). FPO: from i+2 on, exit at the first
                open > entry. Safety max-hold 60 bars (hits reported).
  PRE-COMMITTED CHECKS
    CAL v1 : faithful win rate at the DEFAULT buffer (0.2*ATR) >= 65%.
    POST-RUN AUDIT NOTE (CAL v1 -> v2, TR-27 discipline; verdict tree unedited):
           CAL v1 FAILED (win 35%, 62% stopped, median hold 0d) -- and the transcript
           itself explains why the design was wrong: the video SAYS its demo set the
           buffer LARGER than default ("止損的緩衝區放的比較大"), without publishing
           the value. A claim that is conditional on an unpublished parameter must be
           LOCATED, not assumed at defaults. CAL v2 therefore sweeps the buffer over
           a pre-stated grid {0.2, 0.5, 1.0, 1.5, 2.0, 3.0}*ATR and passes iff some
           buffer reaches win >= 65% (the video's demo region). The sweep is
           calibration/diagnostic, NOT selection: the verdict is judged at the
           SMALLEST claim-matching buffer, and the trap prediction is pre-stated --
           win rate should RISE with buffer while expectancy stays <= 0.
    C1   : expectancy at the claim-matching buffer: net mean P&L/trade, decomposed.
    C2   : ENTRY VALUE (the clean question): 1000 random-entry cohorts of the same
           size per instrument, run through the SAME stop+FPO engine at the SAME
           buffer. PASS iff pooled faithful expectancy > pooled placebo p95.
    C3   : era honesty on SPY: 1993-1998 vs 1999-2026 win rate + expectancy (report;
           small n in-era -- no verdict weight).
  VERDICT RULE (pre-committed):
    CAL fail (no buffer)    -> INVALID-TEST (claim cannot be located in the machine)
    CAL pass, C1 exp <= 0   -> WIN-RATE-TRAP-CONFIRMED (the video's own admission is
                               the whole story: high win rate, negative expectancy)
    CAL pass, C1 > 0, !C2   -> NO-ENTRY-EDGE (expectancy is exit-engine drift; the
                               outside bar adds nothing over random entry)
    CAL pass, C1 > 0, C2    -> ENTRY-EDGE (pattern rehabilitated; era split decides
                               whether it survived publication)
  anti-HARKing : buffer sweep is calibration (locating the source's demo config), with
               the trap prediction pre-stated; verdict judged at the smallest claim-
               matching buffer, never at the best-performing cell; body-filter on/off
               shown only as a diagnostic of TR-30's bug; trials +0 families (same
               family as TR-30, corrected machinery).
  FPO ambiguity note: the transcript mostly says exit checks happen at each day's
               OPEN ("策略會在每天的開盤時檢查"), one clause hints a profitable close
               may also exit; we implement the canonical Williams bailout (first
               profitable OPEN) and note the ambiguity.

Run: uv run python scripts/tests/tr30b_outside_bar_faithful.py   (~2-4 min)
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
COST = 0.0005
BUFFERS = (0.2, 0.5, 1.0, 1.5, 2.0, 3.0)   # x ATR(14); 0.2 = video default, rest = CAL v2 grid
BODY_MULT = 2.0       # video default minRatio
MAX_HOLD = 60         # safety only; hits reported
N_PLACEBO = 1000
SEED = 0
WR_BAR = 0.65         # "extraordinarily high" win-rate calibration bar


def prep(df: pd.DataFrame, body_mult: float | None = BODY_MULT) -> pd.DataFrame:
    d = df.sort_values("ts").reset_index(drop=True)
    ph, pl = d["high"].shift(1), d["low"].shift(1)
    outside = (d["high"] > ph) & (d["low"] < pl)
    sig = outside & (d["close"] < pl)
    if body_mult is not None:
        body = (d["close"] - d["open"]).abs()
        pbody = body.shift(1)
        sig &= (pbody > 0) & (body >= body_mult * pbody)
    d["long_sig"] = sig
    tr = pd.concat([d["high"] - d["low"],
                    (d["high"] - d["close"].shift(1)).abs(),
                    (d["low"] - d["close"].shift(1)).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    return d


def run_trade(o, h, l, c, n, i, stop):
    """Faithful engine: enter open[i+1]; stop with gap-through; FPO from i+2 on.
    Returns (net_return, exit_kind, hold_days) or None if no room."""
    if i + 2 >= n:
        return None
    e = o[i + 1]
    if e <= stop:                       # gapped below stop at entry -> immediate exit
        return -2 * COST, "stop", 0
    if l[i + 1] <= stop:                # stopped intraday on entry day
        return (stop - e) / e - 2 * COST, "stop", 0
    k = i + 2
    while k < n:
        if o[k] <= stop:                # gap through stop -> fill at open
            return (o[k] - e) / e - 2 * COST, "stop", k - (i + 1)
        if o[k] > e:                    # first profitable open
            return (o[k] - e) / e - 2 * COST, "fpo", k - (i + 1)
        if l[k] <= stop:                # intraday stop
            return (stop - e) / e - 2 * COST, "stop", k - (i + 1)
        if k - (i + 1) >= MAX_HOLD:     # safety
            return (c[k] - e) / e - 2 * COST, "maxhold", k - (i + 1)
        k += 1
    return (c[n - 1] - e) / e - 2 * COST, "eod", (n - 1) - (i + 1)


def sim(d: pd.DataFrame, idx: np.ndarray, buffer: float) -> pd.DataFrame:
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    atr = d["atr"].to_numpy()
    n = len(d)
    rows = []
    for i in idx:
        if np.isnan(atr[i]):
            continue
        r = run_trade(o, h, l, c, n, i, l[i] - buffer * atr[i])
        if r is not None:
            rows.append((i, *r))
    return pd.DataFrame(rows, columns=["i", "ret", "kind", "hold"])


def main():
    rng = np.random.default_rng(SEED)
    store = DuckStore("./data")
    print("=" * 100)
    print("TR-30b  OUTSIDE BAR, FAITHFUL ENGINE (machine-fidelity redo; user-audit reopen)")
    print("=" * 100)

    data, sym_pool = {}, []
    for t in INSTR:
        raw = store.load_ohlcv([t])
        if raw.empty:
            continue
        d = prep(raw)
        sig_idx = np.where(d["long_sig"].to_numpy())[0]
        unfiltered = int(prep(raw, body_mult=None)["long_sig"].sum())
        data[t] = (d, sig_idx)
        print(f"  {t}: {len(sig_idx)} faithful signals (2x-body filter kept "
              f"{len(sig_idx)}/{unfiltered} of TR-30's unfiltered set)")
        # symmetric 5d hold on the same entries, for the asymmetry decomposition
        o, c = d["open"].to_numpy(), d["close"].to_numpy()
        ok = sig_idx[sig_idx + 6 < len(d)]
        sym_pool.append((c[ok + 6] - o[ok + 1]) / o[ok + 1] - 2 * COST)
    sym = np.concatenate(sym_pool)
    wr_sym = (sym > 0).mean()

    # ---- CAL v2: locate the video's "high win rate" in buffer space ----
    print("-" * 100)
    print("CAL v2 buffer sweep (win rate / expectancy per trade, pooled 4 ETFs):")
    sweep = {}
    for b in BUFFERS:
        allt = pd.concat([sim(d, idx, b) for d, idx in data.values()], ignore_index=True)
        sweep[b] = allt
        kinds = allt["kind"].value_counts(normalize=True)
        print(f"  buffer {b:.1f}xATR: win {(allt['ret']>0).mean():5.0%} | "
              f"exp {allt['ret'].mean()*100:+.3f}%/trade | fpo {kinds.get('fpo',0):.0%} "
              f"stop {kinds.get('stop',0):.0%} maxhold {kinds.get('maxhold',0):.0%} | "
              f"median hold {allt['hold'].median():.0f}d")
    match = [b for b in BUFFERS if (sweep[b]["ret"] > 0).mean() >= WR_BAR]
    print(f"  (symmetric-5d win rate on the same entries: {wr_sym:.0%})")
    if not match:
        print(f"CAL v2: NO buffer in the grid reaches win rate >= {WR_BAR:.0%} -> FAIL")
        print("VERDICT: INVALID-TEST -- the claim cannot be located in the machine on this seat.")
        return
    B = match[0]           # smallest claim-matching buffer, per F0
    allt = sweep[B]
    wr, exp = (allt["ret"] > 0).mean(), allt["ret"].mean()
    print(f"CAL v2: PASS at buffer {B:.1f}xATR (win {wr:.0%} >= {WR_BAR:.0%}); verdict judged there.")

    # ---- C1 expectancy at the claim-matching buffer ----
    wins, losses = allt.loc[allt["ret"] > 0, "ret"], allt.loc[allt["ret"] <= 0, "ret"]
    c1 = exp > 0
    print(f"C1 expectancy @ {B:.1f}xATR: {exp*100:+.3f}%/trade net | avg win "
          f"{wins.mean()*100:+.3f}% x {wr:.0%} vs avg loss {losses.mean()*100:+.3f}% x "
          f"{1-wr:.0%} | payoff ratio {abs(wins.mean()/losses.mean()):.2f} -> "
          f"{'positive' if c1 else 'NEGATIVE'}")

    # ---- C2 same-engine random-entry placebo at the same buffer ----
    plc_means, sizes = [], []
    for t, (d, sig_idx) in data.items():
        base = np.arange(15, len(d) - 3)
        base = base[~np.isnan(d["atr"].to_numpy()[base])]
        k = len(sim(d, sig_idx, B))
        sizes.append(k)
        pm = np.array([sim(d, rng.choice(base, k, replace=False), B)["ret"].mean()
                       for _ in range(N_PLACEBO)])
        plc_means.append(pm)
    tot = sum(sizes)
    pool_plc = sum(pm * (k / tot) for pm, k in zip(plc_means, sizes))
    p95 = float(np.percentile(pool_plc, 95))
    pctile = float((pool_plc < exp).mean())
    c2 = exp > p95
    print(f"C2 entry value @ {B:.1f}xATR: outside-bar exp {exp*100:+.3f}% vs same-engine "
          f"random-entry p95 {p95*100:+.3f}% (percentile {pctile:.0%}) -> "
          f"{'PASS' if c2 else 'FAIL'}")

    # ---- C3 era split on SPY ----
    d, sig_idx = data["SPY"]
    tr_spy = sim(d, sig_idx, B)
    years = pd.to_datetime(d["ts"]).dt.year.to_numpy()
    for label, a, b_ in (("1993-1998 (in-sample tail)", 1993, 1998),
                         ("1999-2026 (post-publication)", 1999, 2026)):
        w = tr_spy[tr_spy["i"].map(lambda i: a <= years[i] <= b_)]
        if len(w):
            print(f"C3 SPY {label}: n={len(w)}, win {(w['ret']>0).mean():.0%}, "
                  f"exp {w['ret'].mean()*100:+.3f}%")

    if not c1:
        v = ("WIN-RATE-TRAP-CONFIRMED -- the faithful engine reproduces the high win rate "
             "AND the video's admission: expectancy is negative at the claim-matching "
             "buffer. The payoff asymmetry IS the whole story.")
    elif not c2:
        v = ("NO-ENTRY-EDGE -- positive expectancy at the claim-matching buffer is exit-"
             "engine drift: random entries through the same stop+FPO engine do as well.")
    else:
        v = "ENTRY-EDGE -- outside-bar entry beats random entry through the same engine."
    print("-" * 100)
    print(f"VERDICT: {v}")
    print("=" * 100)

    # chart
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    bs = list(BUFFERS)
    wrs = [(sweep[b]["ret"] > 0).mean() * 100 for b in bs]
    exps = [sweep[b]["ret"].mean() * 100 for b in bs]
    ax.plot(bs, wrs, "o-", color="#1565c0", label="win rate (%)")
    ax.axhline(WR_BAR * 100, color="#c62828", ls="--", lw=1, label=f"claim bar {WR_BAR:.0%}")
    ax.axhline(wr_sym * 100, color="#90a4ae", ls=":", lw=1.5, label=f"symmetric-5d {wr_sym:.0%}")
    ax.set_xlabel("stop buffer (xATR14)")
    ax.set_ylabel("win rate (%)", color="#1565c0")
    ax2 = ax.twinx()
    ax2.plot(bs, exps, "s--", color="#c62828", label="expectancy (%/trade)")
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_ylabel("expectancy (%/trade)", color="#c62828")
    ax.set_title("CAL v2: win rate rises with buffer --\ndoes expectancy follow?", fontsize=9.5)
    ax.legend(fontsize=7, loc="center right")
    ax = axes[1]
    ax.bar(["avg win x freq", "avg loss x freq"],
           [wins.mean() * wr * 100, losses.mean() * (1 - wr) * 100],
           color=["#2e7d32", "#c62828"], alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("contribution to expectancy (%/trade)")
    ax.set_title(f"C1 @ {B:.1f}xATR: expectancy = {exp*100:+.3f}%/trade\n"
                 f"win {wr:.0%} x {wins.mean()*100:+.2f}% vs loss {1-wr:.0%} x "
                 f"{losses.mean()*100:+.2f}%", fontsize=9.5)
    ax = axes[2]
    ax.hist(pool_plc * 100, bins=50, color="#90a4ae", alpha=0.8, label="random entry,\nsame engine")
    ax.axvline(p95 * 100, color="#c62828", lw=2, ls="--", label=f"p95 {p95*100:+.3f}%")
    ax.axvline(exp * 100, color="#1565c0", lw=2.5, label=f"outside bar {exp*100:+.3f}%")
    ax.set_xlabel("expectancy (%/trade)")
    ax.set_title(f"C2 @ {B:.1f}xATR: entry value vs same-engine placebo\n"
                 f"(percentile {pctile:.0%})", fontsize=9.5)
    ax.legend(fontsize=8)
    for a in axes:
        a.grid(alpha=0.3)
    fig.suptitle("TR-30b: outside bar, faithful engine (2x body, PHL stop + buffer sweep, true FPO)",
                 fontsize=12)
    fig.tight_layout()
    from pathlib import Path
    outp = Path("docs/tests/img/tr30b_outside_bar_faithful.png")
    fig.savefig(outp, dpi=150)
    plt.close(fig)
    print(f"[chart] {outp}")


if __name__ == "__main__":
    main()
