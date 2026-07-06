"""TR-01 Statistical arbitrage via Engle-Granger cointegration pairs (GGR 2006 style).

TRAIN 2015-2019: EG coint test on log adj_close, same-sector pairs only (SECTORS 47 names),
both orderings, keep top 10 pairs with p<0.05. TRADE 2020-2026 OOS: rolling 252d OLS hedge
ratio (window strictly ending t-1), spread z-score(60), enter dollar-neutral (0.5/0.5 legs)
when |z|>2, exit |z|<0.5, hard stop |z|>4 (blocked until |z|<0.5), positions lagged 1 bar,
net 10bps/leg charged on both legs' turnover. Control: 20 random draws of 10 same-sector
NON-cointegrated pairs (train p>0.5) traded through the identical engine.

Refs: Gatev-Goetzmann-Rouwenhorst (2006) "Pairs Trading: Performance of a Relative-Value
Arbitrage Rule" (RFS); github.com/bradleyboyuyang/Statistical-Arbitrage.

Run: uv run python scripts/tests/tr01_stat_arb_pairs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

logger.remove()

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.tsa.stattools import coint  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sector_strategies as ss  # noqa: E402

from trading_analysis.backtest.metrics import cagr, max_drawdown, sharpe  # noqa: E402
from trading_analysis.data.store import DuckStore  # noqa: E402

TRAIN_START, TRAIN_END = "2015-01-01", "2019-12-31"
OOS_START = "2020-01-01"
IS_START = "2016-07-01"  # in-sample eval window start (after 252+60d warmup)
COST = 0.0010  # 10 bps per leg (single stocks)
ROLL_OLS, ZWIN = 252, 60
Z_IN, Z_OUT, Z_STOP = 2.0, 0.5, 4.0
N_PAIRS = 10
N_CONTROL_DRAWS = 20
MIN_TRAIN_OBS = 1200
SEED = 42
IMG_DIR = ROOT / "docs" / "tests" / "img"


def rolling_hedge(y: pd.Series, x: pd.Series, win: int = ROLL_OLS):
    """OLS y = a + b*x on a rolling window; shifted so params at t use data up to t-1 only."""
    mx, my = x.rolling(win).mean(), y.rolling(win).mean()
    cov = (x * y).rolling(win).mean() - mx * my
    var = (x * x).rolling(win).mean() - mx**2
    beta = cov / var
    alpha = my - beta * mx
    return alpha.shift(1), beta.shift(1)


def zscore(logp: pd.DataFrame, a: str, b: str) -> pd.Series:
    al, be = rolling_hedge(logp[a], logp[b])
    spread = logp[a] - al - be * logp[b]
    return (spread - spread.rolling(ZWIN).mean()) / spread.rolling(ZWIN).std()


def state_machine(z: pd.Series) -> pd.Series:
    """+1 long spread (long leg1/short leg2), -1 short spread; decided at close t."""
    st, blocked = 0, False
    out = np.zeros(len(z))
    for i, zi in enumerate(z.to_numpy()):
        if np.isnan(zi):
            out[i] = st
            continue
        if st == 0:
            if abs(zi) > Z_STOP:
                blocked = True
            if blocked:
                if abs(zi) < Z_OUT:
                    blocked = False
            elif zi > Z_IN:
                st = -1
            elif zi < -Z_IN:
                st = 1
        else:
            if abs(zi) > Z_STOP:  # structural-break hard stop
                st, blocked = 0, True
            elif abs(zi) < Z_OUT:
                st = 0
        out[i] = st
    return pd.Series(out, index=z.index)


def pair_engine(px: pd.DataFrame, logp: pd.DataFrame, a: str, b: str):
    """Full-series net returns, turnover and state for one dollar-neutral pair."""
    st = state_machine(zscore(logp, a, b))
    pos1, pos2 = (st * 0.5).shift(1), (-st * 0.5).shift(1)
    r1, r2 = px[a].pct_change(), px[b].pct_change()
    turn = pos1.diff().abs() + pos2.diff().abs()
    net = (pos1 * r1 + pos2 * r2 - COST * turn).fillna(0.0)
    return net, turn.fillna(0.0), st


def stats(r: pd.Series):
    r = r.dropna()
    eq = (1 + r).cumprod()
    return cagr(eq), sharpe(r), max_drawdown(eq)


def main():
    store = DuckStore(str(ROOT / "data"))
    sectors = ss.SECTORS
    universe = sorted({t for v in sectors.values() for t in v})
    px = store.load_close_pivot([*universe, "QQQ", "VOO", "BIL"], column="adj_close").ffill()
    px.index = pd.to_datetime(px.index)
    logp = np.log(px[[c for c in universe if c in px.columns]])
    lp_train = logp.loc[TRAIN_START:TRAIN_END]

    print("=" * 96)
    print("TR-01 STAT-ARB COINTEGRATION PAIRS (Engle-Granger, GGR 2006 style)")
    print(f"universe {logp.shape[1]} names, data {px.index[0].date()} -> {px.index[-1].date()}")
    print("=" * 96)

    # ---- TRAIN 2015-2019: same-sector EG cointegration scan ----
    rows = []
    for sec, ticks in sectors.items():
        avail = [t for t in ticks if t in lp_train.columns and lp_train[t].notna().sum() >= MIN_TRAIN_OBS]
        for i in range(len(avail)):
            for j in range(i + 1, len(avail)):
                a, b = avail[i], avail[j]
                sub = lp_train[[a, b]].dropna()
                if len(sub) < MIN_TRAIN_OBS:
                    continue
                p_ab = coint(sub[a], sub[b])[1]
                p_ba = coint(sub[b], sub[a])[1]
                if p_ba < p_ab:
                    a, b, p = b, a, p_ba
                else:
                    p = p_ab
                rows.append((sec, a, b, p))
    cand = pd.DataFrame(rows, columns=["sector", "leg1", "leg2", "pval"]).sort_values("pval")
    n_tested = len(cand)
    sel = cand[cand.pval < 0.05].head(N_PAIRS).reset_index(drop=True)
    print(f"train 2015-2019: {n_tested} same-sector pairs tested (x2 orderings = {2 * n_tested} EG tests)")
    print(f"pairs with p<0.05: {(cand.pval < 0.05).sum()}  (expected false positives at 5%: ~{0.05 * n_tested:.0f})")
    print(f"selected top {len(sel)}:")

    # ---- OOS engine on selected pairs ----
    oos_idx = px.loc[OOS_START:].index
    pair_net, pair_turn = {}, {}
    print(f"{'pair':16s} {'sector':14s} {'train_p':>8s} | {'OOS annRet':>10s} {'Sharpe':>7s} {'MDD':>8s} {'trades':>7s} {'active%':>8s}")
    for _, row in sel.iterrows():
        a, b = row.leg1, row.leg2
        net, turn, st = pair_engine(px, logp, a, b)
        key = f"{a}/{b}"
        pair_net[key], pair_turn[key] = net, turn
        n_o, s_o = net.loc[OOS_START:], st.loc[OOS_START:]
        c, sh, mdd = stats(n_o)
        n_trades = int(((s_o != 0) & (s_o.shift(1) == 0)).sum())
        active = float((s_o != 0).mean())
        print(f"{key:16s} {row.sector:14s} {row.pval:8.4f} | {c:+10.2%} {sh:+7.2f} {mdd:+8.2%} {n_trades:7d} {active:8.1%}")

    nets = pd.DataFrame(pair_net)
    turns = pd.DataFrame(pair_turn)
    sleeve = nets.mean(axis=1)  # equal-weight 10 pairs, each 1/10 of sleeve capital
    sleeve_turn = turns.mean(axis=1)
    sl_oos = sleeve.loc[OOS_START:]
    to_ann = float(sleeve_turn.loc[OOS_START:].mean() * 252)

    # ---- benchmarks (OOS) ----
    qqq = px["QQQ"].pct_change().loc[OOS_START:]
    voo = px["VOO"].pct_change().loc[OOS_START:]
    bil = px["BIL"].pct_change().loc[OOS_START:]
    uni_ew = px[logp.columns].pct_change().mean(axis=1).loc[OOS_START:]

    print("-" * 96)
    print(f"OOS window {oos_idx[0].date()} -> {oos_idx[-1].date()}, {len(oos_idx)} days")
    print(f"samples: {len(sel)} pairs x {len(oos_idx)} OOS days = {len(sel) * len(oos_idx)} pair-days")
    print(f"{'series':28s} {'annRet':>8s} {'Sharpe':>7s} {'MDD':>8s}")
    for name, r in [
        ("PAIRS SLEEVE (net 10bps/leg)", sl_oos),
        ("QQQ buy&hold", qqq),
        ("VOO buy&hold", voo),
        ("universe 47 EW buy&hold", uni_ew),
        ("flat cash (BIL)", bil),
    ]:
        c, sh, mdd = stats(r)
        print(f"{name:28s} {c:+8.2%} {sh:+7.2f} {mdd:+8.2%}")
    corr_qqq = float(sl_oos.corr(qqq))
    print(f"sleeve annualized turnover (both legs, one-way): {to_ann:.2f}x of sleeve capital")
    print(f"sleeve corr to QQQ daily returns: {corr_qqq:+.3f}   avg gross exposure: "
          f"{float((nets.loc[OOS_START:] != 0).mean().mean()):.1%} of capital deployed")

    # ---- sub-periods (F7) + in-sample decay reference ----
    print("-" * 96)
    subs = [
        ("IS 2016H2-2019 (selection-biased)", sleeve.loc[IS_START:TRAIN_END]),
        ("OOS 2020-2022", sleeve.loc["2020-01-01":"2022-12-31"]),
        ("OOS 2023-2026", sleeve.loc["2023-01-01":]),
    ]
    for name, r in subs:
        c, sh, mdd = stats(r)
        print(f"{name:34s} annRet {c:+7.2%}  Sharpe {sh:+6.2f}  MDD {mdd:+7.2%}")

    # ---- control: random NON-cointegrated same-sector pairs (train p>0.5) ----
    pool = cand[cand.pval > 0.5].reset_index(drop=True)
    rng = np.random.default_rng(SEED)
    cache: dict[str, pd.Series] = {}
    ctrl_sh, ctrl_ret = [], []
    for _ in range(N_CONTROL_DRAWS):
        pick = pool.iloc[rng.choice(len(pool), size=N_PAIRS, replace=False)]
        rs = []
        for _, rw in pick.iterrows():
            k = f"{rw.leg1}/{rw.leg2}"
            if k not in cache:
                cache[k] = pair_engine(px, logp, rw.leg1, rw.leg2)[0]
            rs.append(cache[k].loc[OOS_START:])
        cr = pd.concat(rs, axis=1).mean(axis=1)
        c, sh, _ = stats(cr)
        ctrl_sh.append(sh)
        ctrl_ret.append(c)
    ctrl_sh, ctrl_ret = np.array(ctrl_sh), np.array(ctrl_ret)
    act_c, act_sh, _act_mdd = stats(sl_oos)
    pct_ctrl_better = float((ctrl_sh >= act_sh).mean())
    print("-" * 96)
    print(f"CONTROL non-coint pairs (p>0.5, pool={len(pool)}): {N_CONTROL_DRAWS} draws x {N_PAIRS} pairs")
    print(f"control Sharpe mean {ctrl_sh.mean():+.2f} [{ctrl_sh.min():+.2f},{ctrl_sh.max():+.2f}]  "
          f"annRet mean {ctrl_ret.mean():+.2%}")
    print(f"share of control draws with Sharpe >= actual ({act_sh:+.2f}): {pct_ctrl_better:.0%}")
    print(f"GGR 2006 claim: ~+11% ann excess (1962-2002); decayed-to-zero post-2010 literature. "
          f"our OOS annRet {act_c:+.2%}")

    # ---- charts ----
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    for r, lab in [(sl_oos, "pairs sleeve (net)"), (qqq, "QQQ"), (uni_ew, "universe 47 EW"), (bil, "BIL cash")]:
        ax[0].plot((1 + r.fillna(0)).cumprod(), label=lab, lw=1.2)
    ax[0].set_title("TR-01 equity, OOS 2020-2026")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=0.3)
    for k in nets.columns:
        ax[1].plot((1 + nets[k].loc[OOS_START:]).cumprod(), lw=0.9, label=k)
    ax[1].set_title("per-pair equity (net, gross=1 when active)")
    ax[1].legend(fontsize=6)
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr01_equity_vs_bench.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    p_sh = [stats(nets[k].loc[OOS_START:])[1] for k in nets.columns]
    ax[0].barh(list(nets.columns), p_sh, color=["#2a9d8f" if x > 0 else "#e76f51" for x in p_sh])
    ax[0].set_title("per-pair OOS Sharpe (net)")
    ax[0].grid(alpha=0.3, axis="x")
    ax[1].hist(ctrl_sh, bins=10, color="#8ab6d6", edgecolor="k", alpha=0.8)
    ax[1].axvline(act_sh, color="#e63946", lw=2, label=f"cointegrated sleeve {act_sh:+.2f}")
    ax[1].set_title(f"control: {N_CONTROL_DRAWS} random non-coint sleeves (Sharpe)")
    ax[1].legend(fontsize=7)
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "tr01_diagnostics.png", dpi=120)
    plt.close(fig)
    print(f"saved {IMG_DIR / 'tr01_equity_vs_bench.png'} and {IMG_DIR / 'tr01_diagnostics.png'}")


if __name__ == "__main__":
    main()
