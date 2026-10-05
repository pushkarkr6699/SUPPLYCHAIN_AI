"""Trained inference for the fixed, registered DataCo order-level pipeline.

No uploaded/caller-selected pickle is loaded. UI scoring requires a successful
offline parity check against every supplied final scored order.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = "models/delivery/DataCo_Tuned_XGBoost.pkl"
PRIMARY_PATH = "data/delivery/final/DataCo_Final_Order_Level_Dataset.csv"
SCORED_PATH = "data/delivery/final/DataCo_Final_Scored_Orders.csv"
VALIDATION_PATH = ROOT / "metadata/inference_validation.json"
REGISTRY_PATH = ROOT / "metadata/data_registry.json"
PORTABLE_REGISTRY_PATH = ROOT / "metadata/portable_model_registry.json"
PORTABLE_PATHS = {"models/delivery/DataCo_Tuned_XGBoost.json", "models/delivery/DataCo_Tuned_XGBoost_Preprocessor.joblib"}
THRESHOLD = 0.35
REQUIRED_PACKAGES = {"scikit-learn": "1.6.1", "xgboost": "3.4.1", "joblib": "1.5.3"}
CATEGORICAL_FEATURES = [
    "Type", "Customer Segment", "Customer Country", "Customer State", "Market",
    "Order Country", "Order Region", "Shipping Mode",
]
NUMERIC_FEATURES = [
    "Order Item Quantity", "Sales", "Order Item Discount", "Order Item Discount Rate",
    "Order Profit Per Order", "Order Item Profit Ratio", "Number_of_Items",
    "Number_of_Products", "Number_of_Categories", "Order_Month", "Order_DayOfWeek",
    "Order_Hour", "Order_Weekend", "Average_Sales_Per_Item", "Average_Quantity_Per_Item",
    "Discount_to_Sales_Ratio", "Profit_Margin", "Order_Complexity",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


class InferenceUnavailable(ValueError):
    """A dependency, artifact or validation issue prevents trained inference."""


def _registered_path(relative: str) -> tuple[Path, str]:
    if relative not in {MODEL_PATH, PRIMARY_PATH, SCORED_PATH}:
        raise InferenceUnavailable("Only fixed registered delivery artifacts are supported.")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise InferenceUnavailable("Registered artifact resolves outside the project.")
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))
    rows = [row for row in registry.get("artifacts", []) if row.get("path") == relative]
    if len(rows) != 1 or not rows[0].get("sha256"):
        raise InferenceUnavailable(f"Missing unique hash registration for {relative}.")
    expected = rows[0]["sha256"]
    if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
        raise InferenceUnavailable(f"Artifact changed or is missing: {relative}. Revalidate before scoring.")
    return path, expected


def _versions() -> dict[str, str]:
    versions = {}
    for name, expected in REQUIRED_PACKAGES.items():
        try:
            actual = metadata.version(name)
        except metadata.PackageNotFoundError as exc:
            raise InferenceUnavailable("Install requirements-inference.txt to enable trained predictions.") from exc
        if actual != expected:
            raise InferenceUnavailable(f"Inference requires {name}=={expected}; found {actual}.")
        versions[name] = actual
    for name in ("numpy", "pandas", "scipy", "threadpoolctl"):
        versions[name] = metadata.version(name)
    return versions


def validate_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Select named features, validate their types and preserve input row order."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise InferenceUnavailable("At least one order with the trained input features is required.")
    if frame.columns.duplicated().any():
        raise InferenceUnavailable("Duplicate input column names are not supported.")
    missing = [column for column in FEATURES if column not in frame]
    if missing:
        raise InferenceUnavailable("Missing model inputs: " + ", ".join(missing))
    result = frame.loc[:, FEATURES].copy()
    for column in NUMERIC_FEATURES:
        try:
            result[column] = pd.to_numeric(result[column], errors="raise").astype(float)
        except (TypeError, ValueError) as exc:
            raise InferenceUnavailable(f"{column} must contain numeric values.") from exc
        if np.isinf(result[column]).any():
            raise InferenceUnavailable(f"{column} cannot contain infinite values.")
    for column in CATEGORICAL_FEATURES:
        if result[column].isna().any() or not result[column].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise InferenceUnavailable(f"{column} requires nonempty text for every order.")
        result[column] = result[column].astype(object)
    return result


@lru_cache(maxsize=1)
def _load_model(expected_hash: str):
    path, digest = _registered_path(MODEL_PATH)
    if digest != expected_hash:
        raise InferenceUnavailable("Registered model changed during loading.")
    _versions()
    import joblib
    from sklearn.pipeline import Pipeline
    from xgboost import XGBClassifier
    portable = _portable_artifacts(expected_hash)
    if portable:
        classifier = XGBClassifier()
        classifier.load_model(portable["models/delivery/DataCo_Tuned_XGBoost.json"])
        model = Pipeline([("preprocessor", joblib.load(portable["models/delivery/DataCo_Tuned_XGBoost_Preprocessor.joblib"])), ("classifier", classifier)])
    else:
        model = joblib.load(path)
    if not isinstance(model, Pipeline) or not isinstance(model.named_steps.get("classifier"), XGBClassifier):
        raise InferenceUnavailable("Artifact is not the expected trained XGBoost pipeline.")
    if list(model.feature_names_in_) != FEATURES or list(model.classes_) != [0, 1]:
        raise InferenceUnavailable("Saved model schema differs from the verified contract.")
    return model


def _portable_artifacts(source_hash: str) -> dict:
    """Accept only fixed, hash-checked exports of the registered original model."""
    if not PORTABLE_REGISTRY_PATH.is_file():
        return {}
    manifest = json.loads(PORTABLE_REGISTRY_PATH.read_text(encoding="utf-8"))
    if manifest.get("source_model_sha256") != source_hash or manifest.get("source_model_path") != MODEL_PATH:
        raise InferenceUnavailable("Portable model provenance differs from the registered original.")
    rows = manifest.get("artifacts", [])
    if len(rows) != 2 or {row.get("path") for row in rows} != PORTABLE_PATHS:
        raise InferenceUnavailable("Unexpected portable model artifacts.")
    result = {}
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise InferenceUnavailable("Portable model artifact changed; reconvert and revalidate.")
        result[row["path"]] = path
    return result


def _validated_context() -> tuple[str, dict]:
    _, digest = _registered_path(MODEL_PATH)
    versions = _versions()
    if not VALIDATION_PATH.is_file():
        raise InferenceUnavailable("Trained inference awaits full scored-output parity validation.")
    report = json.loads(VALIDATION_PATH.read_text(encoding="utf-8-sig"))
    if report.get("status") != "validated" or report.get("model_sha256") != digest:
        raise InferenceUnavailable("Current trained model has no successful parity validation.")
    if _registered_path(PRIMARY_PATH)[1] != report.get("primary_sha256") or _registered_path(SCORED_PATH)[1] != report.get("scored_sha256"):
        raise InferenceUnavailable("Parity reference changed; rerun validation.")
    if report.get("features") != FEATURES or report.get("packages") != versions or report.get("threshold") != THRESHOLD:
        raise InferenceUnavailable("Inference contract or runtime changed; rerun parity validation.")
    portable = _portable_artifacts(digest)
    hashes = {name: sha256(path.read_bytes()).hexdigest() for name, path in portable.items()}
    if report.get("portable_sha256", {}) != hashes:
        raise InferenceUnavailable("Portable model changed; rerun parity validation.")
    return digest, report


def inference_status() -> dict:
    try:
        _, report = _validated_context()
        return {"enabled": True, "model": "Tuned XGBoost", "threshold": THRESHOLD,
                "parity_rows": report["parity_rows"], "reason": "Registered model passed scored-output parity."}
    except OSError:
        return {"enabled": False, "model": "Tuned XGBoost", "reason": "A required delivery model artifact or validation report is unavailable."}
    except (ValueError, KeyError) as exc:
        return {"enabled": False, "model": "Tuned XGBoost", "reason": str(exc)}


def status() -> dict:
    """UI-facing availability, with no model deserialization."""
    state = inference_status()
    return {**state, "available": state["enabled"], "threshold": THRESHOLD}


@lru_cache(maxsize=1)
def _read_primary(digest: str) -> pd.DataFrame:
    path, current = _registered_path(PRIMARY_PATH)
    if current != digest:
        raise InferenceUnavailable("Primary input dataset changed during reading.")
    return pd.read_csv(path)


def input_rows(order_ids=None) -> pd.DataFrame:
    """Return raw registered primary rows, optionally selected by order ID."""
    _, digest = _registered_path(PRIMARY_PATH)
    frame = _read_primary(digest)
    if order_ids is not None:
        frame = frame[frame["Order Id"].astype(str).isin([str(value) for value in order_ids])]
    return frame.copy()


def predict_delivery(frame: pd.DataFrame) -> pd.DataFrame:
    """UI column contract for trained order-level risk predictions."""
    result = score_delivery_orders(frame).rename(columns={
        "Late_Delivery_Probability": "Risk Probability",
        "Predicted_Late_Delivery": "Predicted Late", "Risk_Level": "Risk",
    })
    result["Risk"] = result["Risk"].str.replace(" Risk", "", regex=False)
    result.attrs.update(verified_artifacts=True, live_inference=True, model="Tuned XGBoost", threshold=THRESHOLD)
    return result


def score_delivery_orders(frame: pd.DataFrame) -> pd.DataFrame:
    """Run the validated model on order-level feature rows, retaining their index."""
    features = validate_features(frame)
    digest, _ = _validated_context()
    probability = np.asarray(_load_model(digest).predict_proba(features))[:, 1]
    if not np.isfinite(probability).all() or ((probability < 0) | (probability > 1)).any():
        raise InferenceUnavailable("Model returned an invalid delivery probability.")
    result = pd.DataFrame({
        "Late_Delivery_Probability": probability,
        "Predicted_Late_Delivery": (probability >= THRESHOLD).astype(int),
        "Risk_Level": np.select([probability < 0.40, probability < 0.70], ["Low Risk", "Medium Risk"], default="High Risk"),
        "Prediction_Model": "Tuned XGBoost", "Decision_Threshold": THRESHOLD,
    }, index=frame.index)
    if "Order Id" in frame:
        result.insert(0, "Order Id", frame["Order Id"])
    result.attrs.update(data_source="Live registered Tuned XGBoost inference", model_sha256=digest)
    return result


def validate_registered_delivery_model() -> dict:
    """Explicit offline validation, never an automatic UI side effect."""
    report = {"status": "failed", "validated_at_utc": datetime.now(timezone.utc).isoformat(),
              "model_path": MODEL_PATH, "features": FEATURES, "threshold": THRESHOLD}
    try:
        _, model_hash = _registered_path(MODEL_PATH)
        primary_path, primary_hash = _registered_path(PRIMARY_PATH)
        scored_path, scored_hash = _registered_path(SCORED_PATH)
        report.update(model_sha256=model_hash, primary_sha256=primary_hash, scored_sha256=scored_hash, packages=_versions())
        report["portable_sha256"] = {name: sha256(path.read_bytes()).hexdigest() for name, path in _portable_artifacts(model_hash).items()}
        primary, scored = pd.read_csv(primary_path), pd.read_csv(scored_path)
        if primary["Order Id"].duplicated().any() or scored["Order Id"].duplicated().any():
            raise InferenceUnavailable("Parity requires unique order IDs in both sources.")
        expected = scored.set_index("Order Id")
        inputs = primary.set_index("Order Id").loc[expected.index]
        if len(expected) != 2123 or not (expected["Prediction_Model"] == "Tuned XGBoost").all():
            raise InferenceUnavailable("Expected 2,123-row tuned model parity reference changed.")
        if not np.allclose(expected["Decision_Threshold"], THRESHOLD):
            raise InferenceUnavailable("Parity reference threshold differs from the contract.")
        model = _load_model(model_hash)
        actual = np.asarray(model.predict_proba(validate_features(inputs)))[:, 1]
        error = np.abs(actual - expected["Late_Delivery_Probability"].to_numpy())
        matches = bool(np.array_equal(actual >= THRESHOLD, expected["Predicted_Late_Delivery"].to_numpy()))
        report.update(parity_rows=len(expected), max_absolute_probability_difference=float(error.max()),
                      probability_tolerance=1e-6, all_predicted_labels_match=matches)
        if not np.isfinite(actual).all() or error.max() > 1e-6 or not matches:
            raise InferenceUnavailable("Model output does not reproduce the supplied scored CSV.")
        report.update(status="validated", model_type=type(model.named_steps["classifier"]).__name__,
                      reason="All supplied scored rows reproduced within tolerance; model inference enabled.")
    except Exception as exc:
        report["reason"] = f"{type(exc).__name__}: {exc}"
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate fixed registered delivery model against its scored output.")
    parser.add_argument("--validate", action="store_true", required=True)
    parser.parse_args()
    result = validate_registered_delivery_model()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "validated" else 1)
