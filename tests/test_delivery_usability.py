import pandas as pd
import pytest
from views.delivery import daily_risk_trend


def test_daily_risk_aggregates_intraday_orders_without_filling_missing_scores():
    frame = pd.DataFrame({"Date": pd.to_datetime(["2018-01-05 09:00", "2018-01-04 10:00", "2018-01-04 14:00", "2018-01-04 17:00"]),
                          "Risk Probability": [.7, .2, .8, None]})
    result = daily_risk_trend(frame)
    assert result.Date.tolist() == list(pd.to_datetime(["2018-01-04", "2018-01-05"]))
    assert result["Risk Probability"].tolist() == pytest.approx([.5, .7])
    assert result["Scored orders"].tolist() == [2, 1]
    assert frame.Date.iloc[0].hour == 9


def test_daily_risk_empty_scores_remain_empty():
    frame = pd.DataFrame({"Date": pd.to_datetime(["2018-01-04"]), "Risk Probability": [float("nan")]})
    assert daily_risk_trend(frame).empty
