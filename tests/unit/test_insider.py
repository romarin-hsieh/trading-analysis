import pandas as pd

from trading_analysis.data.connectors.insider import net_purchase_ratio


def test_npr_is_point_in_time_and_leakfree():
    dates = pd.bdate_range("2020-01-01", periods=10)   # 2020-01-01 is a Wednesday
    insider = pd.DataFrame([
        {"symbol": "AAA", "as_of": pd.Timestamp("2020-01-03"), "buy_value": 100.0, "sell_value": 0.0},
        {"symbol": "AAA", "as_of": pd.Timestamp("2020-01-07"), "buy_value": 0.0, "sell_value": 50.0},
    ])
    npr = net_purchase_ratio(insider, dates, ["AAA"], window=252)["AAA"]
    # before the first filing is actionable (snapped to the next trading day) -> NaN
    assert pd.isna(npr.loc[pd.Timestamp("2020-01-02")])
    # buy filed 01-03 -> actionable 01-06 -> all-buys -> NPR = +1
    assert abs(npr.loc[pd.Timestamp("2020-01-06")] - 1.0) < 1e-9
    # sell filed 01-07 -> actionable 01-08 -> (100-50)/(100+50) = +1/3
    assert abs(npr.loc[pd.Timestamp("2020-01-08")] - (1.0 / 3.0)) < 1e-9


def test_npr_missing_symbol_is_nan():
    dates = pd.bdate_range("2021-01-04", periods=5)
    insider = pd.DataFrame([{"symbol": "AAA", "as_of": pd.Timestamp("2021-01-04"),
                             "buy_value": 1.0, "sell_value": 0.0}])
    out = net_purchase_ratio(insider, dates, ["ZZZ"], window=60)
    assert out["ZZZ"].isna().all()
