"""Export the original Linux demand model without fitting or changing it."""
from pathlib import Path
import sys
import json
from hashlib import sha256
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
import numpy as np
import pandas as pd
from services.demand_inference import MODEL, SOURCE, FEATURES, JSON_MODEL, PREPROCESSOR, MANIFEST, registered, historical_inputs
from services.inference_service import _versions

if sys.platform != "linux":
    raise SystemExit("Export this trusted Colab artifact in Linux, then validate on Windows.")
model_path, digest = registered(MODEL)
source, _ = registered(SOURCE)
model = joblib.load(model_path)
if list(model.feature_names_in_) != FEATURES:
    raise ValueError("Unexpected demand feature contract")
frame = historical_inputs(pd.read_csv(source))
prediction = np.maximum(model.predict(frame[FEATURES]), 0)
error = float(np.abs(prediction - frame.Predicted_Next_Day_Visits.to_numpy()).max())
if len(frame) != 1216 or error > 1e-4:
    raise ValueError(f"Demand source parity failed: {error}")
model.named_steps["regressor"].save_model(ROOT / JSON_MODEL)
joblib.dump(model.named_steps["preprocessor"], ROOT / PREPROCESSOR)
manifest = {"source_model_path": MODEL, "source_model_sha256": digest,
            "conversion": "Original fitted preprocessor and XGBRegressor JSON; no retraining",
            "packages": _versions(), "source_parity_rows": len(frame), "source_max_difference": error,
            "artifacts": [{"path": path, "sha256": sha256((ROOT / path).read_bytes()).hexdigest()} for path in (JSON_MODEL, PREPROCESSOR)]}
MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
