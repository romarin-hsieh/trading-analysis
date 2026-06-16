"""Fundamental factor builders — point-in-time, economically-motivated, leak-free.

Each builder turns the SEC-EDGAR fundamentals panel (long form, with `as_of` = filing date)
into a [date x symbol] factor frame, aligned strictly point-in-time via `edgar.point_in_time`
(uses only facts filed on/before each date). Flow variables (NetIncome, GrossProfit, CFO) are
taken from annual filings (fp == "FY") for consistent 12-month scale; balance-sheet stocks
(Assets, Equity, shares) use the latest filed value.

Factors are signed so that HIGHER = predicted-better (long the high end):
  gross_profitability  GrossProfit/Assets               (Novy-Marx 2013)
  roa                  NetIncome/Assets                 (quality)
  accruals             -(NetIncome - CFO)/Assets        (Sloan 1996: high accruals -> low returns)
  earnings_yield       NetIncome/MarketCap              (value)
  book_to_market       Equity/MarketCap                 (Fama-French value)
  asset_growth         -(Assets/Assets_1y - 1)          (Cooper-Gulen-Schill 2008)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trading_analysis.data.connectors.edgar import point_in_time


def _fy(fund: pd.DataFrame) -> pd.DataFrame:
    """Annual filings only (fp == 'FY') — clean 12-month flow values."""
    return fund[fund["fp"] == "FY"]


def _shares(fund: pd.DataFrame, dates, syms) -> pd.DataFrame:
    sh = point_in_time(fund, "CommonStockSharesOutstanding", dates, syms)
    wa = point_in_time(_fy(fund), "WeightedAverageNumberOfSharesOutstandingBasic", dates, syms)
    return sh.where(sh.notna(), wa)


def gross_profitability(fund, dates, syms) -> pd.DataFrame:
    gp = point_in_time(_fy(fund), "GrossProfit", dates, syms)
    return gp / point_in_time(fund, "Assets", dates, syms)


def roa(fund, dates, syms) -> pd.DataFrame:
    ni = point_in_time(_fy(fund), "NetIncomeLoss", dates, syms)
    return ni / point_in_time(fund, "Assets", dates, syms)


def accruals(fund, dates, syms) -> pd.DataFrame:
    ni = point_in_time(_fy(fund), "NetIncomeLoss", dates, syms)
    cfo = point_in_time(_fy(fund), "NetCashProvidedByUsedInOperatingActivities", dates, syms)
    at = point_in_time(fund, "Assets", dates, syms)
    return -((ni - cfo) / at)


def earnings_yield(fund, px: pd.DataFrame, syms) -> pd.DataFrame:
    ni = point_in_time(_fy(fund), "NetIncomeLoss", px.index, syms)
    mcap = px[syms] * _shares(fund, px.index, syms)
    return ni / mcap.where(mcap > 0)


def book_to_market(fund, px: pd.DataFrame, syms) -> pd.DataFrame:
    eq = point_in_time(fund, "StockholdersEquity", px.index, syms)
    mcap = px[syms] * _shares(fund, px.index, syms)
    return eq / mcap.where(mcap > 0)


def asset_growth(fund, dates, syms, lookback: int = 252) -> pd.DataFrame:
    at = point_in_time(fund, "Assets", dates, syms)
    return -(at / at.shift(lookback) - 1.0)


def _zscore(f: pd.DataFrame) -> pd.DataFrame:
    return f.sub(f.mean(axis=1), axis=0).div(f.std(axis=1).replace(0, np.nan), axis=0)


def quality_composite(fund, dates, syms) -> pd.DataFrame:
    """Equal-weight composite of the profitability/quality signals (cross-sectional z-scores of
    gross_profitability + roa + accruals). Averaging diversifies the noise of any single metric —
    the test is whether the composite is MORE robust (stable IC) than gross profitability alone."""
    zs = [_zscore(gross_profitability(fund, dates, syms)),
          _zscore(roa(fund, dates, syms)),
          _zscore(accruals(fund, dates, syms))]
    stack = np.nanmean(np.stack([z.to_numpy(dtype=float) for z in zs]), axis=0)
    return pd.DataFrame(stack, index=dates, columns=list(syms))


def build_all(fund, px, syms) -> dict[str, pd.DataFrame]:
    """All fundamental factors as point-in-time wide frames, keyed by name."""
    dates = px.index
    return {
        "gross_profitability": gross_profitability(fund, dates, syms),
        "roa": roa(fund, dates, syms),
        "accruals": accruals(fund, dates, syms),
        "earnings_yield": earnings_yield(fund, px, syms),
        "book_to_market": book_to_market(fund, px, syms),
        "asset_growth": asset_growth(fund, dates, syms),
    }
