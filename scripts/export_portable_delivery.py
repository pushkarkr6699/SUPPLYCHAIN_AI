"""Convert only the registered trusted delivery pipeline to portable artifacts.

Run in Linux with requirements-inference.txt when a Colab XGBoost pickle cannot
be read by Windows. Original files are retained. No model is fitted or modified.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
from services.inference_service import (
    MODEL_PATH, PRIMARY_PATH, SCORED_PATH, FEATURES, _registered_path, _versions,
    validate_features,
)


def main():
    if sys.platform != "linux":
        raise SystemExit("Run this conversion in Linux; validate the exported artifacts on the target runtime afterward.")
    path, source_hash = _registered_path(MODEL_PATH)
    primary_path, _ = _registered_path(PRIMARY_PATH)
    scored_path, _ = _registered_path(SCORED_PATH)
    packages = _versions()
    model = joblib.load(path)
    if list(model.feature_names_in_) != FEATURES:
        raise ValueError("Unexpected trained feature schema")
    primary = pd.read_csv(primary_path).set_index("Order Id")
    expected = pd.read_csv(scored_path).set_index("Order Id")
    probabilities = model.predict_proba(validate_features(primary.loc[expected.index]))[:, 1]
    maximum_error = float(np.abs(probabilities - expected["Late_Delivery_Probability"].to_numpy()).max())
    if len(expected) != 2123 or maximum_error > 1e-6:
        raise ValueError(f"Source pipeline failed parity: {len(expected)} rows; max error {maximum_error}")
    model_path = ROOT / "models/delivery/DataCo_Tuned_XGBoost.json"
    preprocessing_path = ROOT / "models/delivery/DataCo_Tuned_XGBoost_Preprocessor.joblib"
    model.named_steps["classifier"].save_model(model_path)
    joblib.dump(model.named_steps["preprocessor"], preprocessing_path)
    manifest = {
        "source_model_path": MODEL_PATH, "source_model_sha256": source_hash,
        "conversion": "XGBClassifier.save_model JSON and original fitted preprocessing, no retraining",
        "source_platform": sys.platform, "packages": packages,
        "source_parity_rows": len(expected), "source_max_probability_difference": maximum_error,
        "artifacts": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (model_path, preprocessing_path)
        ],
    }
    (ROOT / "metadata/portable_model_registry.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
