import pandas as pd

from trading_analysis.factors.fundamentals import accruals, gross_profitability, roa


def _setup():
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08"])
    px = pd.DataFrame(100.0, index=dates, columns=["AAA"])
    fund = pd.DataFrame([
        {"symbol": "AAA", "tag": "NetIncomeLoss", "fp": "FY", "period_end": "2019-12-31", "as_of": "2020-01-06", "val": 10.0},
        {"symbol": "AAA", "tag": "GrossProfit", "fp": "FY", "period_end": "2019-12-31", "as_of": "2020-01-06", "val": 40.0},
        {"symbol": "AAA", "tag": "NetCashProvidedByUsedInOperatingActivities", "fp": "FY", "period_end": "2019-12-31", "as_of": "2020-01-06", "val": 12.0},
        {"symbol": "AAA", "tag": "Assets", "fp": "FY", "period_end": "2019-12-31", "as_of": "2020-01-06", "val": 100.0},
    ])
    fund["as_of"] = pd.to_datetime(fund["as_of"])
    fund["period_end"] = pd.to_datetime(fund["period_end"])
    return fund, px, dates


def test_roa_is_point_in_time():
    fund, _, dates = _setup()
    r = roa(fund, dates, ["AAA"])["AAA"]
    assert pd.isna(r.loc[dates[0]])                                  # before the 2020-01-06 filing
    assert abs(r.loc[pd.Timestamp("2020-01-06")] - 0.10) < 1e-9      # 10/100, known only after filing
    assert abs(r.loc[pd.Timestamp("2020-01-08")] - 0.10) < 1e-9


def test_gross_profitability_value():
    fund, _, dates = _setup()
    g = gross_profitability(fund, dates, ["AAA"])["AAA"]
    assert abs(g.loc[pd.Timestamp("2020-01-07")] - 0.40) < 1e-9      # 40/100


def test_accruals_sign():
    # accruals factor = -(NI - CFO)/Assets ; NI 10 > CFO 12? here NI-CFO = -2 -> factor = +0.02
    fund, _, dates = _setup()
    a = accruals(fund, dates, ["AAA"])["AAA"]
    assert abs(a.loc[pd.Timestamp("2020-01-07")] - 0.02) < 1e-9
