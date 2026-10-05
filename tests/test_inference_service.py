import json
from hashlib import sha256

import numpy as np
import pandas as pd
import pytest

from services import inference_service as service


def _features():
    values = {name: ["Known category"] for name in service.CATEGORICAL_FEATURES}
    values.update({name: [1.0] for name in service.NUMERIC_FEATURES})
    return pd.DataFrame(values, index=[42])


def test_feature_validation_rejects_missing_and_invalid_inputs():
    frame = _features()
    with pytest.raises(service.InferenceUnavailable, match="Missing model inputs"):
        service.validate_features(frame.drop(columns="Shipping Mode"))
    frame["Sales"] = "invalid"
    with pytest.raises(service.InferenceUnavailable, match="numeric"):
        service.validate_features(frame)
    frame["Sales"] = np.inf
    with pytest.raises(service.InferenceUnavailable, match="infinite"):
        service.validate_features(frame)


def test_registry_rejects_changed_artifact_before_loading(tmp_path, monkeypatch):
    path = tmp_path / service.MODEL_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(b"original registered model")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"artifacts": [{"path": service.MODEL_PATH, "sha256": sha256(path.read_bytes()).hexdigest()}]}))
    monkeypatch.setattr(service, "ROOT", tmp_path)
    monkeypatch.setattr(service, "REGISTRY_PATH", registry)
    assert service._registered_path(service.MODEL_PATH)[0] == path
    path.write_bytes(b"replaced artifact")
    with pytest.raises(service.InferenceUnavailable, match="changed"):
        service._registered_path(service.MODEL_PATH)
    with pytest.raises(service.InferenceUnavailable, match="fixed registered"):
        service._registered_path("uploaded_model.pkl")


def test_failed_parity_disables_scoring(tmp_path, monkeypatch):
    report = tmp_path / "validation.json"
    report.write_text(json.dumps({"status": "failed", "model_sha256": "abc"}))
    monkeypatch.setattr(service, "VALIDATION_PATH", report)
    monkeypatch.setattr(service, "_registered_path", lambda path: (tmp_path / path, "abc"))
    monkeypatch.setattr(service, "_versions", lambda: {})
    monkeypatch.setattr(service, "_load_model", lambda _: pytest.fail("Blocked model must not load"))
    assert not service.status()["available"]
    with pytest.raises(service.InferenceUnavailable, match="successful parity"):
        service.predict_delivery(_features())


def test_prediction_preserves_index_and_separates_risk_band_from_threshold(monkeypatch):
    class KnownModel:
        def predict_proba(self, frame):
            assert list(frame.columns) == service.FEATURES
            return np.array([[0.65, 0.35]])

    monkeypatch.setattr(service, "_validated_context", lambda: ("verified-hash", {}))
    monkeypatch.setattr(service, "_load_model", lambda _: KnownModel())
    frame = _features()
    frame["Order Id"] = 123
    result = service.predict_delivery(frame)
    assert result.index.tolist() == [42]
    assert result.loc[42, "Order Id"] == 123
    assert result.loc[42, "Predicted Late"] == 1
    assert result.loc[42, "Risk"] == "Low"
    assert result.attrs["live_inference"] is True
