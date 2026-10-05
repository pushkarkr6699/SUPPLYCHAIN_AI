import numpy as np
import pandas as pd
import pytest
from services.demand_inference import historical_inputs, InferenceUnavailable


def history():
    return pd.DataFrame({"DateOnly": pd.date_range("2020-01-01", periods=16), "Product": "A", "Category": "C", "Department": "D", "Visits": np.arange(16), "Next_Day_Visits": 999999})


def test_demand_features_use_only_current_and_past_visits():
    frame = history()
    result = historical_inputs(frame)
    assert len(result) == 2
    row = result.iloc[0]
    assert row.Visits == 14
    assert row.Visits_Lag_1 == 13
    assert row.Visits_Lag_7 == 7
    assert row.Rolling_Mean_14 == 6.5
    frame.Next_Day_Visits = -12345
    pd.testing.assert_frame_equal(result.drop(columns="Next_Day_Visits"), historical_inputs(frame).drop(columns="Next_Day_Visits"))


def test_demand_history_refuses_gaps_duplicates_and_negative_visits():
    with pytest.raises(InferenceUnavailable, match="consecutive"):
        historical_inputs(history().drop(index=3))
    with pytest.raises(InferenceUnavailable, match="unique"):
        historical_inputs(pd.concat([history(), history().iloc[:1]]))
    frame = history()
    frame.loc[0, "Visits"] = -1
    with pytest.raises(InferenceUnavailable, match="nonnegative"):
        historical_inputs(frame)
