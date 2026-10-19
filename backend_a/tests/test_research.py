import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from decision_policy import LABELS, POLICY_VERSION, recommendation_from_risk, risk_from_probabilities, synthetic_label
from generate_artifacts import collect_embeddings, training_cases
from research.audit import audit, file_hash
from research.evaluate import evaluate, metrics, proportion, validate_rows
from research.infer import predict_dataset


def row(case_id, label, probabilities):
    return {"case_id": case_id, "label": label, "probabilities": probabilities,
            "age_months": 24, "missing_vitals": 0, "sex": "F"}


def document(rows):
    return {"rows": rows, "metadata": {"data_kind": "synthetic", "policy_version": POLICY_VERSION,
                                       "dataset_sha256": "a" * 64, "checkpoint_sha256": "b" * 64}}


def test_policy_matches_production_decisions_instead_of_argmax():
    from inference.predict import _risk_to_recommendation

    probabilities = [0.48, 0.03, 0.49]
    assert LABELS[probabilities.index(max(probabilities))] == "911"
    assert _risk_to_recommendation(risk_from_probabilities(probabilities)) == "ED"
    assert recommendation_from_risk(risk_from_probabilities([9.254421942585678e-15, 2.504457721123985e-14, 1.0])) == "911"
    for threshold, expected in [(0.0, "HOME"), (0.35, "ED"), (0.70, "911"), (1.0, "911")]:
        assert recommendation_from_risk(threshold) == expected
    for invalid in [[0.1, 0.2, 0.3], [float("nan"), 0, 1], [-0.1, 0.1, 1], [True, 0, 0], []]:
        with pytest.raises(ValueError):
            risk_from_probabilities(invalid)
    with pytest.raises(ValueError):
        synthetic_label("unknown diagnosis")


def test_metrics_count_misses_false_alarms_and_do_not_call_absent_classes_safe():
    rows = [row("a", "911", [1, 0, 0]), row("b", "HOME", [0, 0, 1]), row("c", "ED", [0, 1, 0])]
    report = evaluate(document(rows))
    overall = report["overall"]
    assert overall["confusion_matrix"] == [[0, 0, 1], [0, 1, 0], [1, 0, 0]]
    assert overall["accuracy"]["estimate"] == 1 / len(rows)
    assert overall["per_class"]["911"]["missed"] == 1
    assert overall["per_class"]["911"]["false_alarms"] == 1
    assert overall["undertriage"]["estimate"] == overall["overtriage"]["estimate"] == 1 / len(rows)
    assert overall["multiclass_brier"] == (2 + 2 + 0) / len(rows)
    assert report["clinical_validation"] is False
    absent = metrics([row("a", "HOME", [1, 0, 0])])
    assert absent["per_class"]["911"]["sensitivity"]["estimate"] is None
    assert absent["per_class"]["911"]["precision"]["estimate"] is None
    assert proportion(0, 0)["wilson_95"] is None
    assert proportion(0, 10)["wilson_95"][1] > 0
    assert proportion(10, 10)["wilson_95"][0] < 1


def test_perfect_probabilities_have_zero_brier_and_calibration_error():
    rows = [row(str(i), label, [int(j == i) for j in range(len(LABELS))]) for i, label in enumerate(LABELS)]
    overall = evaluate(document(rows))["overall"]
    assert overall["multiclass_brier"] == 0
    assert all(group["ece"] == 0 for group in overall["calibration"].values())
    assert sum(bin_["n"] for bin_ in overall["calibration"]["HOME"]["bins"]) == len(rows)


def test_invalid_or_duplicate_rows_and_unbound_artifacts_are_rejected():
    good = row("a", "HOME", [1, 0, 0])
    for rows in [[], [good, good], [{**good, "age_months": 216}], [{**good, "missing_vitals": -1}], [{**good, "label": "maybe"}]]:
        with pytest.raises(ValueError):
            validate_rows(rows)
    invalid = document([good]); invalid["metadata"]["checkpoint_sha256"] = "missing"
    with pytest.raises(ValueError, match="identity"):
        evaluate(invalid)


def test_cohort_audit_detects_template_overlap_and_future_information():
    first = {"patient_id": "a", "complaint_text": "fever 3 days; reassessment at 30 minutes", "ground_truth": "sepsis", "vitals": {}}
    second = {**first, "patient_id": "b", "complaint_text": "fever 5 days; reassessment at 30 minutes"}
    report = audit([first], [second])
    assert report["overlap"]["patient_ids"] == 0
    assert report["overlap"]["numeric_normalized_complaints"] == 1
    assert report["cohorts"]["evaluation"]["complaints_with_later_information"] == 1
    assert report["arrival_evaluation_ready"] is False


def test_missing_checkpoint_and_leakage_fail_before_model_loading(tmp_path):
    dataset, checkpoint = tmp_path / "cases.json", tmp_path / "model.pt"
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        predict_dataset(dataset, checkpoint, "synthetic")
    checkpoint.write_bytes(b"not a model")
    dataset.write_text(json.dumps([{"complaint_text": "On reassessment at 30 minutes"}]))
    with pytest.raises(ValueError, match="post-arrival"):
        predict_dataset(dataset, checkpoint, "synthetic")
    with pytest.raises(ValueError, match="post-arrival"):
        predict_dataset(dataset, checkpoint, "real", allow_legacy=True)


def test_auxiliary_artifacts_require_training_membership():
    cohort = [{"patient_id": "a"}, {"patient_id": "b"}]
    assert training_cases(cohort, {"train_patient_ids": ["a"], "validation_patient_ids": ["b"]}) == [cohort[0]]
    for meta in [{}, {"train_patient_ids": ["a"], "validation_patient_ids": ["a"]}, {"train_patient_ids": ["a"], "validation_patient_ids": ["c"]}]:
        with pytest.raises(ValueError):
            training_cases(cohort, meta)


def test_artifact_embeddings_match_the_live_normalized_input_path():
    import numpy as np
    import torch
    from models.fusion import FusionModel, RoryModel
    from models.vitals_mlp import VitalsMLP

    class FixedText(torch.nn.Module):
        def forward(self, texts):
            return torch.ones((len(texts), 128))

    torch.manual_seed(7)
    vitals = VitalsMLP(dropout=0.0)
    model = RoryModel(vitals, FixedText(), FusionModel(dropout=0.0)).eval()
    case = {"vitals": {"hr": 140, "rr": None, "temp_f": 103, "spo2": 96, "cap_refill_s": 3},
            "complaint_text": "Synthetic test", "ground_truth": "sepsis"}
    with torch.inference_mode():
        expected = model([case["vitals"]], [case["complaint_text"]])["fused_emb"].numpy()
        raw = torch.tensor([[140, 26, 103, 96, 3, 0, 1, 0, 0, 0]], dtype=torch.float32)
        incorrect = model(raw, [case["complaint_text"]])["fused_emb"].numpy()
    embeddings, centroid_inputs = collect_embeddings(model, [case])
    np.testing.assert_array_equal(embeddings, expected)
    np.testing.assert_array_equal(centroid_inputs, expected)
    assert not np.allclose(embeddings, incorrect)


def test_evaluation_cli_binds_reference_labels_and_dataset_bytes(tmp_path):
    dataset, predictions, output = [tmp_path / name for name in ("cases.json", "predictions.json", "report.json")]
    dataset.write_text(json.dumps([{"patient_id": "a", "ground_truth": "sepsis", "age_months": 24, "sex": "F", "vitals": {}}]))
    content = document([{**row("a", "911", [0, 0, 1]), "missing_vitals": 5}])
    content["metadata"]["dataset_sha256"] = file_hash(dataset)
    predictions.write_text(json.dumps(content))
    cmd = [sys.executable, "-m", "research.evaluate", "--dataset", str(dataset), "--predictions", str(predictions), "--output", str(output)]
    cwd = Path(__file__).parents[1]
    assert subprocess.run(cmd, cwd=cwd, capture_output=True).returncode == 0
    assert json.loads(output.read_text())["overall"]["n"] == 1
    output.unlink()
    altered = copy.deepcopy(content); altered["rows"][0]["label"] = "HOME"
    predictions.write_text(json.dumps(altered))
    assert subprocess.run(cmd, cwd=cwd, capture_output=True).returncode != 0
    assert not output.exists()
    overwrite = cmd[:-1] + [str(dataset)]
    original = dataset.read_bytes()
    assert subprocess.run(overwrite, cwd=cwd, capture_output=True).returncode != 0
    assert dataset.read_bytes() == original
    predictions.write_text(json.dumps(content)); dataset.write_text("[]")
    assert subprocess.run(cmd, cwd=cwd, capture_output=True).returncode != 0
    assert not output.exists()
