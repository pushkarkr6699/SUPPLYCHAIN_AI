"""Strict, read-only adapters for supplied scored CSV artifacts.

Only CSV outputs are loaded. Serialized model files are deliberately not loaded;
the available delivery file contains pre-scored predictions and the forecast file
contains precomputed product/day forecasts.
"""
from functools import lru_cache
from pathlib import Path
import pandas as pd
import numpy as np


DELIVERY_COLUMNS = {
    "Order Id", "Market", "Order Region", "Order Country", "Category Name",
    "Department Name", "Customer Segment", "Shipping Mode", "Order_Date",
    "Actual_Late_Delivery", "Late_Delivery_Probability", "Predicted_Late_Delivery",
    "Correct_Prediction", "Delivery_Risk_Level",
}
DEMAND_COLUMNS = {
    "DateOnly", "Product", "Category", "Department", "Next_Day_Visits",
    "Predicted_Next_Day_Visits", "Error", "Absolute_Error", "Prediction_Lower_90",
    "Prediction_Upper_90", "Demand_Level", "Stock_Attention_Flag",
}
THRESHOLD_COLUMNS = {"Threshold", "Accuracy", "Balanced_Accuracy", "Precision", "Recall", "F1", "MCC"}
DELIVERY_MODEL_COLUMNS = {"Model", "Accuracy", "Balanced_Accuracy", "Precision", "Recall", "F1", "ROC_AUC", "PR_AUC", "MCC"}
FEATURE_COLUMNS = {"Feature", "Importance"}


@lru_cache(maxsize=8)
def _read_csv(path_text, modified_ns, size):
    return pd.read_csv(path_text)


def _read(path, required, name):
    source = Path(path).expanduser().resolve(strict=True)
    if source.suffix.lower() != ".csv" or not source.is_file():
        raise ValueError(f"{name} must be a readable CSV file.")
    frame = _read_csv(str(source), source.stat().st_mtime_ns, source.stat().st_size).copy()
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {', '.join(sorted(missing))}")
    return frame, source


def delivery_records(path):
    raw, source = _read(path, DELIVERY_COLUMNS, "Delivery scored output")
    numeric = ["Late_Delivery_Probability", "Actual_Late_Delivery", "Predicted_Late_Delivery", "Correct_Prediction"]
    raw["Order_Date"] = pd.to_datetime(raw["Order_Date"], errors="raise")
    raw[numeric] = raw[numeric].apply(pd.to_numeric, errors="raise")
    if raw[numeric].isna().any().any() or not raw.Late_Delivery_Probability.between(0, 1).all():
        raise ValueError("Delivery scored output contains missing or out-of-range predictions.")
    if any(not raw[column].isin([0, 1]).all() for column in numeric[1:]):
        raise ValueError("Delivery outcomes, predictions, and correctness values must be binary.")
    if not raw.Delivery_Risk_Level.isin(["Low Risk", "Medium Risk", "High Risk"]).all():
        raise ValueError("Delivery scored output contains an unsupported risk label.")
    if not (raw.Predicted_Late_Delivery.astype(int) == (raw.Late_Delivery_Probability >= .56).astype(int)).all():
        raise ValueError("Scored predictions do not match the verified 0.56 threshold.")
    if not (raw.Correct_Prediction.astype(int) == (raw.Predicted_Late_Delivery == raw.Actual_Late_Delivery).astype(int)).all():
        raise ValueError("Correct_Prediction does not match the supplied actual and predicted labels.")
    frame = pd.DataFrame({
        "Order": raw["Order Id"].astype(str), "Date": raw["Order_Date"], "Market": raw["Market"],
        "Region": raw["Order Region"], "Country": raw["Order Country"], "Category": raw["Category Name"],
        "Department": raw["Department Name"], "Customer Segment": raw["Customer Segment"],
        "Shipping Mode": raw["Shipping Mode"], "Risk Probability": raw["Late_Delivery_Probability"],
        "Risk": raw["Delivery_Risk_Level"].str.replace(" Risk", "", regex=False),
        "Actual Late": raw["Actual_Late_Delivery"].astype(bool),
        "Predicted Late": raw["Predicted_Late_Delivery"].astype(bool),
        "Correct Prediction": raw["Correct_Prediction"].astype(bool),
    })
    frame.attrs.update(data_source="Verified scored delivery CSV", artifact=source.name,
                       artifact_rows=len(frame), duplicate_rows=int(frame.duplicated().sum()),
                       model_loaded=False, production_threshold=.56)
    return frame


def demand_records(path):
    raw, source = _read(path, DEMAND_COLUMNS, "Demand forecast output")
    numeric = ["Next_Day_Visits", "Predicted_Next_Day_Visits", "Error", "Absolute_Error", "Prediction_Lower_90", "Prediction_Upper_90"]
    raw["DateOnly"] = pd.to_datetime(raw["DateOnly"], errors="raise")
    raw[numeric] = raw[numeric].apply(pd.to_numeric, errors="raise")
    nonnegative = ["Next_Day_Visits", "Predicted_Next_Day_Visits", "Absolute_Error", "Prediction_Lower_90", "Prediction_Upper_90"]
    if raw[numeric].isna().any().any() or (raw[nonnegative] < 0).any().any():
        raise ValueError("Demand forecast output contains missing or negative values.")
    if not (raw.Error.sub(raw.Next_Day_Visits - raw.Predicted_Next_Day_Visits).abs() < .001).all():
        raise ValueError("Demand Error values do not match actual minus predicted demand.")
    if not (raw.Absolute_Error.sub(raw.Error.abs()).abs() < .001).all():
        raise ValueError("Demand Absolute_Error values do not match Error.")
    if raw.duplicated(["DateOnly", "Product"]).any():
        raise ValueError("Demand output must contain one row per forecast date and product.")
    if not (raw.Prediction_Lower_90 <= raw.Prediction_Upper_90).all():
        raise ValueError("Demand prediction interval bounds are inverted.")
    covered = raw.Next_Day_Visits.between(raw.Prediction_Lower_90, raw.Prediction_Upper_90)
    frame = pd.DataFrame({
        "Date": raw["DateOnly"], "Product": raw["Product"], "Category": raw["Category"],
        "Department": raw["Department"], "Actual Demand": raw["Next_Day_Visits"],
        "Forecast Demand": raw["Predicted_Next_Day_Visits"], "Lower": raw["Prediction_Lower_90"],
        "Upper": raw["Prediction_Upper_90"], "Forecast Error": raw["Error"],
        "Absolute Error": raw["Absolute_Error"], "Demand Level": raw["Demand_Level"],
        "Stock Attention": raw["Stock_Attention_Flag"].eq("Review Stock"),
    })
    frame.attrs.update(data_source="Verified product/day demand forecast CSV", artifact=source.name,
                       artifact_rows=len(frame), interval_label="source labels bounds as 90%",
                       observed_interval_coverage=float(covered.mean()), model_loaded=False)
    return frame


def order_delivery_records(primary_path, scored_path):
    """Attach d1 scores to the unique-order analytical source; retain missing scores."""
    required = {"Order Id", "Order_Date", "Late_delivery_risk", "Market", "Order Region", "Order Country", "Shipping Mode", "Customer Segment"}
    primary, source = _read(primary_path, required, "Primary delivery dataset")
    score_required = {"Order Id", "Late_Delivery_Probability", "Predicted_Late_Delivery", "Risk_Level", "Prediction_Model", "Decision_Threshold"}
    scored, score_source = _read(scored_path, score_required, "Final delivery scored orders")
    for frame in (primary, scored):
        if frame["Order Id"].isna().any() or frame["Order Id"].duplicated().any():
            raise ValueError("Delivery sources must have unique, non-null Order Id values.")
    primary["Order_Date"] = pd.to_datetime(primary["Order_Date"], errors="raise")
    if primary.Order_Date.isna().any() or not primary.Late_delivery_risk.isin([0, 1]).all():
        raise ValueError("Delivery dates and binary target labels must be complete.")
    probability = pd.to_numeric(scored.Late_Delivery_Probability, errors="raise")
    if not np.isfinite(probability).all() or not probability.between(0, 1).all():
        raise ValueError("Delivery probabilities must be finite values in [0, 1].")
    thresholds = pd.to_numeric(scored.Decision_Threshold, errors="raise").unique()
    if len(thresholds) != 1 or not 0 <= thresholds[0] <= 1:
        raise ValueError("Scored orders must specify one valid decision threshold.")
    threshold = float(thresholds[0])
    if not scored.Predicted_Late_Delivery.isin([0, 1]).all() or not scored.Predicted_Late_Delivery.eq(probability.ge(threshold).astype(int)).all():
        raise ValueError("Scored predictions do not match the supplied decision threshold.")
    if not scored.Risk_Level.isin(["Low Risk", "Medium Risk", "High Risk"]).all():
        raise ValueError("Scored orders contain unsupported risk labels.")
    if not scored["Order Id"].isin(primary["Order Id"]).all():
        raise ValueError("Scored orders contain IDs absent from the primary dataset.")
    indexed = primary.set_index("Order Id").loc[scored["Order Id"]].reset_index()
    for column in (set(primary.columns) & set(scored.columns)) - {"Order Id"}:
        a, b = indexed[column].reset_index(drop=True), scored[column].reset_index(drop=True)
        if column == "Order_Date":
            matched = a.eq(pd.to_datetime(b, errors="raise")).all()
        elif pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            matched = np.isclose(a, b, rtol=1e-9, atol=1e-8, equal_nan=True).all()
        else:
            matched = a.astype("string").eq(b.astype("string")).fillna(False).all()
        if not matched:
            raise ValueError(f"Scored output disagrees with primary data for {column}.")
    scores = scored[["Order Id", "Late_Delivery_Probability", "Predicted_Late_Delivery", "Risk_Level"]].copy()
    frame = primary.merge(scores, on="Order Id", how="left", validate="one_to_one", sort=False)
    frame = frame.rename(columns={"Order Id": "Order", "Order_Date": "Date", "Order Country": "Country", "Order Region": "Region",
        "Late_delivery_risk": "Actual Late", "Order Profit Per Order": "Profit", "Late_Delivery_Probability": "Risk Probability",
        "Predicted_Late_Delivery": "Predicted Late", "Risk_Level": "Risk"})
    frame["Order"] = frame.Order.astype(str)
    frame["Actual Late"] = frame["Actual Late"].astype(bool)
    frame["Predicted Late"] = frame["Predicted Late"].astype("boolean")
    frame["Correct Prediction"] = frame["Predicted Late"].eq(frame["Actual Late"])
    frame["Risk"] = frame.Risk.astype("string").str.replace(" Risk", "", regex=False)
    frame.attrs.update(data_source="DataCo primary orders + supplied Tuned XGBoost scores", artifact=source.name,
        score_artifact=score_source.name, verified_artifacts=True, dataset="delivery", artifact_rows=len(frame), primary_rows=len(frame),
        scored_rows=len(scored), duplicate_rows=0, production_threshold=threshold, model_name="Tuned XGBoost",
        feature_importance_model="Random Forest baseline", model_loaded=False,
        evaluation_note="January 2018 retrospective test predictions; threshold 0.35 was selected using this same test set.")
    return frame


def threshold_records(path):
    raw, source = _read(path, THRESHOLD_COLUMNS, "Threshold analysis output")
    raw = raw.sort_values("Threshold").reset_index(drop=True)
    if raw.empty or raw[list(THRESHOLD_COLUMNS)].isna().any().any():
        raise ValueError("Threshold analysis output is empty or incomplete.")
    if not raw.Threshold.between(0, 1).all():
        raise ValueError("Threshold values must be between zero and one.")
    raw.attrs.update(data_source="Verified threshold analysis CSV", artifact=source.name)
    return raw


def tabular_artifact(path, required, name):
    """Load a small, non-executable CSV metadata artifact with a strict schema."""
    raw, source = _read(path, required, name)
    if raw.empty:
        raise ValueError(f"{name} is empty.")
    raw.attrs.update(data_source=f"Verified {name}", artifact=source.name)
    return raw


def summary_artifact(path):
    raw, source = _read(path, {"Property", "Value"}, "Delivery final summary")
    if raw.empty or raw.Property.duplicated().any():
        raise ValueError("Delivery final summary must contain unique metric names.")
    result = dict(zip(raw.Property.astype(str), raw.Value))
    return result, source.name


def text_artifact(path, name):
    source = Path(path).expanduser().resolve(strict=True)
    if source.suffix.lower() != ".txt" or not source.is_file():
        raise ValueError(f"{name} must be a readable TXT file.")
    value = source.read_text(encoding="utf-8").strip()
    if not value or len(value) > 200:
        raise ValueError(f"{name} is empty or unexpectedly long.")
    return value, source.name
