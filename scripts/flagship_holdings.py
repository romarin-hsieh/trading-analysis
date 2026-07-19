"""Flagship holdings -- exactly what the book holds TODAY, and what is fixed vs what moves.

The recipe (5 sleeves, their rules, the allocator) is FIXED and pre-registered. Two of
the five sleeves are RULES over a universe, so their line items change at each 21-day
rebalance; three are single instruments. This script prints/exports both layers so the
book is reproducible line-by-line rather than only at the sleeve level.

Outputs exports/dashboard/flagship_holdings.json and a console sheet.
Run: uv run python scripts/flagship_holdings.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

logger.remove()
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

import leveraged_strategies as ls  # noqa: E402
import sector_strategies as ss  # noqa: E402
import validate_recommendation as vr  # noqa: E402

from trading_analysis.portfolio import rebalance  # noqa: E402

SLEEVE_ZH = {
    "equity_mom": "科技/AI 動能輪動(規則,持股每月換)",
    "defensive": "防禦性雙動能輪動(規則,持股每月換)",
    "lev_trend": "趨勢閘門 TQQQ(單一標的,開/關)",
    "gold": "黃金 GLD(單一標的,買進持有)",
    "bonds": "美債 IEF(單一標的,買進持有)",
}


def main():
    rp, _ew, sleeves = vr.build_combo()
    W = rebalance(sleeves, lookback=126, step=21, method="risk_parity")
    w_now = W.iloc[-1]
    asof = str(sleeves.index[-1].date())

    allsyms = sorted({s for v in ss.SECTORS.values() for s in v})
    # every sleeve is read at the SAME as-of as the book itself (the store's tail rows are
    # only partially refreshed; mixing as-ofs would rank stale prices against fresh ones)
    asof_ts = sleeves.index[-1]
    px = ss._px(allsyms).loc[:asof_ts]
    spy = ss._spy().reindex(px.index).ffill()

    # sleeve 1: which names does the momentum rule hold right now?
    held = ss.momentum_trend_direction(px, spy, k=10, hold=21, regime=True)
    row = held.iloc[-1]
    eq_names = sorted(row[row > 0].index.tolist())
    spy_on = bool((spy > spy.rolling(200, min_periods=150).mean()).iloc[-1])

    # sleeve 2: dual momentum. strat_dual_momentum returns (metrics_dict, result) and does
    # NOT expose its selection frame, so the rule is replicated here verbatim (lines 99-129
    # of sector_strategies). An earlier version indexed [0] expecting a frame, silently hit
    # the empty branch, and PRINTED a fabricated "all-defensive" state -- never let a
    # display layer invent a position; fail loudly instead.
    defensive_assets = ("IEF", "TLT", "GLD")
    syms_d = list(dict.fromkeys(list(allsyms) + list(defensive_assets)))
    pxd = ss._px(syms_d).loc[:asof_ts]
    spyd = ss._spy().reindex(pxd.index).ffill()
    lp = np.log(pxd)
    mom12 = lp.shift(1) - lp.shift(252)
    risk_cols = [s for s in allsyms if s in pxd.columns]
    def_cols = [s for s in defensive_assets if s in pxd.columns]
    if not risk_cols or not def_cols:
        raise RuntimeError("defensive sleeve: universe columns missing -- refusing to guess")
    spy_off = ~((spyd > spyd.rolling(200, min_periods=150).mean())
                .shift(1).reindex(pxd.index).ffill().fillna(False))
    rebal_d = pd.Series(False, index=pxd.index)
    rebal_d.iloc[::21] = True
    last_rebal = pxd.index[rebal_d.values][-1]
    mrow = mom12.loc[last_rebal]
    drow = mrow[def_cols].dropna().sort_values(ascending=False)
    if drow.empty:
        raise RuntimeError("defensive sleeve: no defensive momentum at the last rebalance")
    if bool(spy_off.loc[last_rebal]):
        def_names = [s for s in drow.index if drow[s] > 0][:4]
        def_mode = "risk-off(SPY 在 200 日均線下)"
    else:
        rk = mrow[risk_cols].dropna().sort_values(ascending=False)
        bond_mom = float(drow.max())
        def_names = [s for s in rk.index[:4] if rk[s] > 0 and rk[s] > bond_mom]
        n_empty = 4 - len(def_names)
        if n_empty > 0:
            def_names += [s for s in drow.index if drow[s] > 0][:n_empty]
        def_mode = "risk-on(需 12 個月動能為正且贏過最佳防禦資產)"

    # sleeve 3: trend gate state
    qqq_on = bool(ls._trend("QQQ", 200).ffill().loc[:asof_ts].iloc[-1])

    print("=" * 96)
    print(f"主力 5-sleeve 組合 —— 實際持倉表(資料截至 {asof})")
    print("=" * 96)
    print("【固定不變的部分:配方本身】")
    print("  1) 五條 sleeve 的定義與規則參數(下方),2) 逆波動風險平價配置器(126 日回看、21 日再平衡),")
    print("     3) 決策一律用前一日資料、隔日生效(無前視)。TR-25 已證:權重 ±20-25% 微調不改結論。")
    print()
    print("【每月會變的部分:權重 + 兩條規則 sleeve 的持股】")
    print(f"  市場閘門狀態:SPY > 200 日均線 = {spy_on} | QQQ > 200 日均線 = {qqq_on}")
    print()
    print(f"{'sleeve':<12}{'權重':>8}   說明 / 現在實際持有")
    print("-" * 96)
    lines = {}
    for k in ("equity_mom", "defensive", "lev_trend", "gold", "bonds"):
        w = float(w_now[k])
        if k == "equity_mom":
            detail = (", ".join(eq_names) if eq_names else "(閘門關閉或無名單 → 空手)")
            hold = eq_names
        elif k == "defensive":
            detail = (f"{', '.join(def_names)}   [{def_mode}]" if def_names
                      else f"空手(規則判定無合格標的;{def_mode})")
            hold = def_names
        elif k == "lev_trend":
            detail = "TQQQ 持有" if qqq_on else "空手(QQQ 在 200 日均線下)"
            hold = ["TQQQ"] if qqq_on else []
        elif k == "gold":
            detail, hold = "GLD", ["GLD"]
        else:
            detail, hold = "IEF", ["IEF"]
        lines[k] = {"weight": round(w, 4), "holdings": hold, "rule": SLEEVE_ZH[k]}
        print(f"{k:<12}{w:>7.1%}   {SLEEVE_ZH[k]}")
        print(f"{'':<12}{'':>8}   → {detail}")
    print("-" * 96)
    print("規則規格(可逐條重現):")
    print("  equity_mom:宇宙=47 檔主題股(AI/半導體 16、軟體 10、太空軍工 13、機器人 8);")
    print("             選股=126 日動能(跳過最近 21 日)取前 10,且需 價>50SMA>150SMA;")
    print("             每 21 日換股;跌破 50SMA 當日出場;SPY<200SMA 時整條清空。")
    print("  defensive :Antonacci 雙動能——12 個月絕對動能為正、且贏過最佳防禦資產(IEF/TLT/GLD)")
    print("             才持有前 4 名;SPY<200SMA 直接轉防禦資產;每 21 日再判。")
    print("  lev_trend :QQQ>200SMA 才持有 TQQQ,否則空手(這是唯一的槓桿腿)。")
    print("  gold/bonds:GLD 與 IEF 買進持有,由配置器決定比重。")
    print()
    print("誠實但書:equity_mom 的 47 檔宇宙是**人工挑選的主題清單**(docs/07),不是機械式全市場篩選")
    print("——這是已登記的選擇偏誤來源(docs/13 §11 對同類清單量測過 +62.8% 的幻覺);")
    print("該 sleeve 的權重只有約 1 成,且 TR-11 的隨機視窗檢定已對它降級為『動能≈beta』。")

    out = {
        "meta": {"source": "trading-analysis", "as_of": asof,
                 "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "fixed": "sleeve definitions + rule parameters + inverse-vol risk-parity "
                          "(126d lookback, 21d rebalance, decisions lagged one bar)",
                 "moves": "allocator weights (monthly) and the line items inside the two "
                          "rule-based sleeves (21d rebalance)",
                 "gates": {"spy_above_200sma": spy_on, "qqq_above_200sma": qqq_on},
                 "caveat": "equity_mom universe is a hand-curated 47-name thematic list "
                           "(docs/07) -- a registered selection-bias source; ~11% weight; "
                           "TR-11 downgraded that sleeve to 'momentum = beta'"},
        "sleeves": lines,
    }
    Path("exports/dashboard").mkdir(parents=True, exist_ok=True)
    Path("exports/dashboard/flagship_holdings.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n[export] exports/dashboard/flagship_holdings.json")


if __name__ == "__main__":
    main()
