import pandas as pd
import pytest
from services.verified_data import order_delivery_records
from services.analytics import classification, summary, threshold_curve


def sources(tmp_path):
    primary = pd.DataFrame([
        {"Order Id": 1, "Order_Date": "2018-01-01", "Late_delivery_risk": 1, "Market": "Europe", "Order Region": "West", "Order Country": "France", "Shipping Mode": "Standard Class", "Customer Segment": "Consumer"},
        {"Order Id": 2, "Order_Date": "2017-12-01", "Late_delivery_risk": 1, "Market": "Europe", "Order Region": "West", "Order Country": "France", "Shipping Mode": "Standard Class", "Customer Segment": "Consumer"},
    ])
    scored = pd.DataFrame([{"Order Id": 1, "Late_Delivery_Probability": .4, "Predicted_Late_Delivery": 1, "Risk_Level": "Medium Risk", "Prediction_Model": "Tuned XGBoost", "Decision_Threshold": .35}])
    primary_path, scored_path = tmp_path / "primary.csv", tmp_path / "scored.csv"
    primary.to_csv(primary_path, index=False)
    scored.to_csv(scored_path, index=False)
    return primary, scored, primary_path, scored_path


def test_partial_score_join_retains_primary_orders_and_missing_predictions(tmp_path):
    _, _, primary, scored = sources(tmp_path)
    frame = order_delivery_records(primary, scored)
    assert len(frame) == 2 and frame.attrs["scored_rows"] == 1
    assert pd.isna(frame.loc[1, "Risk Probability"])
    assert pd.isna(frame.loc[1, "Risk"]) and pd.isna(frame.loc[1, "Predicted Late"])
    assert frame.attrs["production_threshold"] == .35
    assert summary(frame)["accuracy"] == 1
    assert classification(frame, .35)["Scored Rows"] == 1
    assert classification(frame, .35)["FN"] == 0
    assert .35 in threshold_curve(frame).Threshold.values
    assert summary(frame.iloc[1:])["accuracy"] is None


@pytest.mark.parametrize("bad_case", ["unknown_id", "duplicate_id", "threshold_mismatch", "primary_disagreement"])
def test_misaligned_scored_artifacts_fail_closed(tmp_path, bad_case):
    primary, scored, primary_path, scored_path = sources(tmp_path)
    if bad_case == "unknown_id":
        scored["Order Id"] = 99
    elif bad_case == "duplicate_id":
        primary["Order Id"] = 1
    elif bad_case == "threshold_mismatch":
        scored["Predicted_Late_Delivery"] = 0
    else:
        scored["Market"] = "Wrong market"
    primary.to_csv(primary_path, index=False)
    scored.to_csv(scored_path, index=False)
    with pytest.raises(ValueError):
        order_delivery_records(primary_path, scored_path)
