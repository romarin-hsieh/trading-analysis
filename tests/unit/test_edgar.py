import pandas as pd

from trading_analysis.data.connectors.edgar import point_in_time


def _fund(rows):
    df = pd.DataFrame(rows)
    df["as_of"] = pd.to_datetime(df["as_of"])
    df["period_end"] = pd.to_datetime(df["period_end"])
    return df


def test_point_in_time_is_leakfree():
    # a fact only appears in the factor on/after its FILED (as_of) date, never before
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06",
                            "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"])
    fund = _fund([
        {"symbol": "AAA", "tag": "Assets", "period_end": "2019-12-31", "as_of": "2020-01-06", "val": 100.0},
        {"symbol": "AAA", "tag": "Assets", "period_end": "2020-03-31", "as_of": "2020-01-09", "val": 120.0},
    ])
    out = point_in_time(fund, "Assets", dates, ["AAA"])["AAA"]
    assert pd.isna(out.loc[pd.Timestamp("2020-01-02")])     # before first filing -> unknown
    assert pd.isna(out.loc[pd.Timestamp("2020-01-03")])
    assert out.loc[pd.Timestamp("2020-01-06")] == 100.0     # known from its filing date onward
    assert out.loc[pd.Timestamp("2020-01-08")] == 100.0
    assert out.loc[pd.Timestamp("2020-01-09")] == 120.0     # superseded by the newer filing
    assert out.loc[pd.Timestamp("2020-01-10")] == 120.0


def test_point_in_time_picks_latest_period_in_a_filing():
    # one 10-K re-discloses a prior year as a comparative (same as_of) -> use the CURRENT period
    dates = pd.to_datetime(["2021-02-01", "2021-02-02"])
    fund = _fund([
        {"symbol": "BBB", "tag": "Assets", "period_end": "2020-12-31", "as_of": "2021-02-01", "val": 200.0},
        {"symbol": "BBB", "tag": "Assets", "period_end": "2019-12-31", "as_of": "2021-02-01", "val": 150.0},
    ])
    out = point_in_time(fund, "Assets", dates, ["BBB"])["BBB"]
    assert out.loc[pd.Timestamp("2021-02-01")] == 200.0     # latest period_end, not the comparative
    assert out.loc[pd.Timestamp("2021-02-02")] == 200.0


def test_point_in_time_missing_symbol_is_nan():
    dates = pd.to_datetime(["2021-01-04", "2021-01-05"])
    fund = _fund([{"symbol": "AAA", "tag": "Assets", "period_end": "2020-12-31",
                   "as_of": "2021-01-04", "val": 1.0}])
    out = point_in_time(fund, "Assets", dates, ["ZZZ"])
    assert out["ZZZ"].isna().all()
