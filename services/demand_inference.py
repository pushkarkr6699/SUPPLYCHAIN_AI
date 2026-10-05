"""Next-day web-visit forecasts using the original fitted demand pipeline."""
from functools import lru_cache
from hashlib import sha256
import json
import numpy as np
import pandas as pd
from services.inference_service import ROOT, REGISTRY_PATH, _versions, InferenceUnavailable

MODEL = "models/demand/AccessLogs_Final_XGBoost_Demand_Model.pkl"
SOURCE = "data/demand/final/AccessLogs_Final_Advanced_Forecast.csv"
JSON_MODEL = "models/demand/AccessLogs_Final_XGBoost_Demand_Model.json"
PREPROCESSOR = "models/demand/AccessLogs_Final_XGBoost_Demand_Preprocessor.joblib"
MANIFEST = ROOT / "metadata/portable_demand_registry.json"
VALIDATION = ROOT / "metadata/demand_inference_validation.json"
FEATURES = ["Product", "Category", "Department", "Visits", "Visits_Lag_1", "Visits_Lag_2",
            "Visits_Lag_7", "Rolling_Mean_3", "Rolling_Mean_7", "Rolling_Mean_14",
            "Rolling_Std_7", "Month", "DayOfWeek", "Weekend", "DayOfMonth"]


def registered(relative):
    if relative not in {MODEL, SOURCE}:
        raise InferenceUnavailable("Only registered demand artifacts are accepted.")
    rows = json.loads(REGISTRY_PATH.read_text(encoding="utf-8-sig"))["artifacts"]
    rows = [row for row in rows if row["path"] == relative]
    path = (ROOT / relative).resolve()
    if len(rows) != 1 or not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != rows[0]["sha256"]:
        raise InferenceUnavailable("Demand artifact changed or is missing; revalidate.")
    return path, rows[0]["sha256"]


def historical_inputs(raw):
    """Use current visits and strictly earlier visits; target is never an input."""
    required = {"DateOnly", "Product", "Category", "Department", "Visits"}
    if not required.issubset(raw.columns):
        raise InferenceUnavailable("Daily history requires DateOnly, Product, Category, Department and Visits.")
    frame = raw.copy()
    frame["DateOnly"] = pd.to_datetime(frame.DateOnly, errors="raise").dt.normalize()
    frame["Visits"] = pd.to_numeric(frame.Visits, errors="raise")
    if frame[list(required)].isna().any().any() or not np.isfinite(frame.Visits).all() or (frame.Visits < 0).any() or frame.duplicated(["Product", "DateOnly"]).any():
        raise InferenceUnavailable("Daily history must have unique product/date rows and complete nonnegative visits.")
    frame = frame.sort_values(["Product", "DateOnly"]).reset_index(drop=True)
    for _, group in frame.groupby("Product", sort=False):
        if len(group) < 15 or not group.DateOnly.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise InferenceUnavailable("Each product needs at least 15 consecutive daily visits rows; include zero-visit days.")
        if group.Category.nunique() != 1 or group.Department.nunique() != 1:
            raise InferenceUnavailable("Product category and department must be stable within the history.")
    grouped = frame.groupby("Product", sort=False).Visits
    for lag in (1, 2, 7):
        frame[f"Visits_Lag_{lag}"] = grouped.shift(lag)
    for window in (3, 7, 14):
        frame[f"Rolling_Mean_{window}"] = grouped.transform(lambda series: series.shift(1).rolling(window, min_periods=1).mean())
    frame["Rolling_Std_7"] = grouped.transform(lambda series: series.shift(1).rolling(7, min_periods=2).std()).fillna(0)
    frame["Month"] = frame.DateOnly.dt.month
    frame["DayOfWeek"] = frame.DateOnly.dt.dayofweek
    frame["Weekend"] = frame.DayOfWeek.ge(5).astype(int)
    frame["DayOfMonth"] = frame.DateOnly.dt.day
    return frame[frame.groupby("Product").cumcount().ge(14)].copy()


def portable_artifacts():
    _, digest = registered(MODEL)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("source_model_sha256") != digest or manifest.get("source_model_path") != MODEL:
        raise InferenceUnavailable("Demand conversion provenance differs from the original model.")
    rows = manifest.get("artifacts", [])
    if len(rows) != 2 or {row.get("path") for row in rows} != {JSON_MODEL, PREPROCESSOR}:
        raise InferenceUnavailable("Unexpected demand model exports.")
    hashes = {}
    for row in rows:
        path = (ROOT / row["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise InferenceUnavailable("Demand model export changed; revalidate.")
        hashes[row["path"]] = row["sha256"]
    return digest, hashes


@lru_cache(maxsize=1)
def load_model(digest, hashes):
    import joblib
    from sklearn.pipeline import Pipeline
    from xgboost import XGBRegressor
    current, artifacts = portable_artifacts()
    if current != digest or tuple(sorted(artifacts.items())) != hashes:
        raise InferenceUnavailable("Demand model changed during loading.")
    regressor = XGBRegressor()
    regressor.load_model(ROOT / JSON_MODEL)
    pipeline = Pipeline([("preprocessor", joblib.load(ROOT / PREPROCESSOR)), ("regressor", regressor)])
    if list(pipeline.feature_names_in_) != FEATURES:
        raise InferenceUnavailable("Demand feature schema differs from its training contract.")
    return pipeline


def context():
    versions = _versions()
    digest, hashes = portable_artifacts()
    report = json.loads(VALIDATION.read_text(encoding="utf-8"))
    _, source_hash = registered(SOURCE)
    if report.get("status") != "validated" or report.get("model_sha256") != digest or report.get("portable_sha256") != hashes or report.get("source_sha256") != source_hash or report.get("packages") != versions or report.get("features") != FEATURES:
        raise InferenceUnavailable("Demand inference awaits successful runtime parity validation.")
    return digest, tuple(sorted(hashes.items())), report


def status():
    try:
        _, _, report = context()
        return {"available": True, "parity_rows": report["parity_rows"], "reason": "Trained XGBoost web-visit model validated."}
    except OSError:
        return {"available": False, "reason": "Demand model artifacts or validation report are missing or unreadable. Check Model Health and offline validation."}
    except (ValueError, KeyError) as exc:
        return {"available": False, "reason": str(exc)}


def predict_next_day(history):
    digest, hashes, _ = context()
    frame = historical_inputs(history).groupby("Product", sort=False).tail(1)
    probability = np.maximum(load_model(digest, hashes).predict(frame[FEATURES]), 0)
    if not np.isfinite(probability).all():
        raise InferenceUnavailable("Demand model returned invalid forecasts.")
    output = frame[["Product", "Category", "Department", "DateOnly"]].copy().rename(columns={"DateOnly": "Base Date"})
    output["Forecast Date"] = output["Base Date"] + pd.Timedelta(days=1)
    output["Predicted Visits"] = probability
    output.attrs.update(live_inference=True, verified_artifacts=True, data_source="Live registered XGBoost web-visit inference", model="XGBoost", units="web visits", model_sha256=digest)
    return output.reset_index(drop=True)


def validate():
    report = {"status": "failed", "features": FEATURES, "model_path": MODEL}
    try:
        digest, hashes = portable_artifacts()
        path, source_hash = registered(SOURCE)
        report.update(model_sha256=digest, portable_sha256=hashes, source_sha256=source_hash, packages=_versions())
        frame = historical_inputs(pd.read_csv(path))
        actual = np.maximum(load_model(digest, tuple(sorted(hashes.items()))).predict(frame[FEATURES]), 0)
        error = np.abs(actual - frame.Predicted_Next_Day_Visits.to_numpy())
        report.update(parity_rows=len(frame), max_absolute_difference=float(error.max()), tolerance=1e-4)
        if len(frame) != 1216 or not np.isfinite(actual).all() or error.max() > 1e-4:
            raise InferenceUnavailable("Reconstructed demand model inputs do not reproduce supplied forecasts.")
        report.update(status="validated", reason="1,216 complete-history supplied forecasts reproduced; first 14 days excluded.")
    except Exception as exc:
        report["reason"] = f"{type(exc).__name__}: {exc}"
    VALIDATION.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "validated" else 1)
