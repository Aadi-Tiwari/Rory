import importlib
import builtins

import pytest


def test_missing_checkpoint_fails_before_constructing_or_downloading_models(tmp_path, monkeypatch):
    predictor = importlib.import_module("inference.predict")
    monkeypatch.setattr(predictor, "_model", None)
    monkeypatch.setattr(predictor, "MODEL_PATH", tmp_path / "missing.pt")

    original_import = builtins.__import__

    def no_model_import(name, *args, **kwargs):
        if name == "torch" or name.startswith("models."):
            raise AssertionError("Model imports must not run without a checkpoint")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_model_import)
    with pytest.raises(FileNotFoundError, match="checkpoint is unavailable"):
        predictor._load_model()


def test_api_reports_missing_assets_without_returning_a_prediction(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from inference import main

    predictor = importlib.import_module("inference.predict")
    missing = tmp_path / "missing.pt"
    monkeypatch.setattr(predictor, "_model", None)
    monkeypatch.setattr(predictor, "MODEL_PATH", missing)
    monkeypatch.setattr(main, "MODEL_PATH", missing)
    with TestClient(main.app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["checkpoint_present"] is False
        response = client.post("/predict", json={
            "patient_id": "test-only", "age_months": 144, "sex": "M",
            "weight_kg": 40, "complaint_text": "Synthetic test input", "vitals": {},
        })
    assert response.status_code == 503
    assert "recommendation" not in response.json()
