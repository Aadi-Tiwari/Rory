from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from backend_a.validation.metrics import rate, summarize
from backend_a.validation.retrospective import (
    freeze, make_report, read_json_hashed, sha256, validate_cohort, verify_manifest, write_json,
)


@pytest.fixture
def study():
    return {
        "setting": "pediatric_ed", "reference_standard": "test fixture only",
        "clinical_review_status": "approved", "horizon_hours": 24,
        "cohort_role": "exploratory", "development_sites": ["development"],
        "development_end": "2025-01-01T00:00:00Z", "baseline_name": "recorded screen",
    }


@pytest.fixture
def cohort():
    feature = {"value": 100, "observed_at": "2026-01-01T09:00:00Z",
               "available_at": "2026-01-01T09:01:00Z"}
    row = {
        "patient_id": "fixture-only", "encounter_id": "visit", "site_id": "evaluation",
        "age_months": 120, "index_time": "2026-01-01T09:02:00Z",
        "complaint": {**feature, "value": "Fictional complaint for a unit test.",
                      "origin": "recorded_at_care"},
        "vitals": {"hr": feature, "rr": None, "temp_f": None, "spo2": None, "cap_refill_s": None},
        "units": {"hr": "bpm", "rr": "breaths/min", "temp_f": "degF",
                  "spo2": "percent", "cap_refill_s": "seconds"},
        "outcome": {"sepsis": 1, "prevalent_sepsis": False,
                    "onset_time": "2026-01-01T13:00:00Z",
                    "followup_end": "2026-01-02T09:02:00Z", "ascertainment_complete": True},
        "baseline": None,
    }
    return {
        "dataset_kind": "real", "dataset_id": "unit-test-fixture", "setting": "pediatric_ed",
        "reference_standard": "test fixture only", "clinical_review_status": "approved",
        "access_basis": "fabricated unit test", "patient_linkage": "one test patient",
        "sampling_description": "fabricated unit test", "calendar_time_preserved": True,
        "records": [row],
    }


def test_valid_record_preserves_missingness(cohort, study):
    rows = validate_cohort(cohort, study, set())
    assert rows[0]["vitals"]["temp_f"] is None


@pytest.mark.parametrize("field,value", [
    ("dataset_kind", "synthetic"), ("setting", "icu"),
    ("clinical_review_status", "pending"), ("patient_linkage", ""),
    ("reference_standard", "different outcome"),
])
def test_cohort_mismatch_is_rejected(cohort, study, field, value):
    cohort[field] = value
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


@pytest.mark.parametrize("field,value", [
    ("available_at", "2026-01-01T10:00:00Z"),
    ("observed_at", "2026-01-01T10:00:00Z"),
    ("available_at", "2026-01-01T09:01:00"),
])
def test_future_and_ambiguous_predictors_are_rejected(cohort, study, field, value):
    cohort["records"][0]["complaint"][field] = value
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


@pytest.mark.parametrize("field,value", [("value", ""), ("origin", "generated_from_diagnosis")])
def test_missing_or_reconstructed_text_is_rejected(cohort, study, field, value):
    cohort["records"][0]["complaint"][field] = value
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_patient_separation(cohort, study):
    with pytest.raises(ValueError, match="overlap"):
        validate_cohort(cohort, study, {"fixture-only"})
    cohort["records"].append(deepcopy(cohort["records"][0]))
    with pytest.raises(ValueError, match="Repeated"):
        validate_cohort(cohort, study, set())


@pytest.mark.parametrize("field,value", [
    ("onset_time", "2026-01-01T09:02:00Z"),
    ("onset_time", "2026-01-03T00:00:00Z"),
    ("followup_end", "2026-01-01T12:59:00Z"),
    ("ascertainment_complete", False),
    ("prevalent_sepsis", True), ("sepsis", True),
])
def test_invalid_outcomes_are_rejected(cohort, study, field, value):
    cohort["records"][0]["outcome"][field] = value
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_negative_outcome_requires_complete_followup(cohort, study):
    outcome = cohort["records"][0]["outcome"]
    outcome.update(sepsis=0, onset_time=None)
    assert validate_cohort(cohort, study, set())
    outcome["followup_end"] = "2026-01-01T13:00:00Z"
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_known_positive_does_not_require_followup_after_the_event(cohort, study):
    cohort["records"][0]["outcome"]["followup_end"] = "2026-01-01T13:00:00Z"
    assert validate_cohort(cohort, study, set())


def test_external_site_must_be_unseen(cohort, study):
    study["cohort_role"] = "external"
    cohort["records"][0]["site_id"] = "development"
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_temporal_cohort_requires_real_dates_and_known_site(cohort, study):
    study["cohort_role"] = "temporal"
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())
    cohort["records"][0]["site_id"] = "development"
    cohort["calendar_time_preserved"] = False
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())
    cohort["calendar_time_preserved"] = True
    assert validate_cohort(cohort, study, set())
    study["development_end"] = "2027-01-01T00:00:00Z"
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_baseline_must_be_available_at_index(cohort, study):
    cohort["records"][0]["baseline"] = {
        "name": "recorded screen", "value": 1,
        "observed_at": "2026-01-01T09:00:00Z", "available_at": "2026-01-01T10:00:00Z",
    }
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


@pytest.mark.parametrize("bad_age", [-1, 216, float("nan"), True])
def test_age_population(cohort, study, bad_age):
    cohort["records"][0]["age_months"] = bad_age
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_units_and_nonfinite_vitals(cohort, study):
    cohort["records"][0]["units"]["temp_f"] = "degC"
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())
    cohort["records"][0]["units"]["temp_f"] = "degF"
    cohort["records"][0]["vitals"]["hr"]["value"] = float("nan")
    with pytest.raises(ValueError):
        validate_cohort(cohort, study, set())


def test_binary_metrics_and_undefined_denominators():
    report = summarize([0, 0, 1, 1], [0.1, 0.8, 0.2, 0.9], .7, 40)
    assert report["confusion"] == dict(tp=1, fp=1, tn=1, fn=1)
    assert report["auroc"] == pytest.approx(3 / 4)
    assert report["average_precision"] == pytest.approx((1 + 2 / 3) / 2)
    assert report["sensitivity"]["value"] == pytest.approx(1 / 2)
    assert rate(0, 0)["value"] is None
    assert rate(0, 10)["ci95"][1] > 0
    assert rate(10, 10)["ci95"][0] < 1
    absent = summarize([0, 0], [0.1, 0.2], .7, 10)
    assert absent["sensitivity"]["value"] is None
    assert absent["auroc"] is None


def test_ties_and_reproducible_intervals():
    a = summarize([0, 0, 1, 1], [.5] * 4, .7, 30)
    b = summarize([0, 0, 1, 1], [.5] * 4, .7, 30)
    assert a == b
    assert a["auroc"] == pytest.approx(1 / 2)
    assert a["average_precision"] == pytest.approx(1 / 2)


@pytest.mark.parametrize("successes,total", [(0, 7), (2, 11), (7, 7)])
def test_rate_intervals_against_scipy(successes, total):
    from scipy.stats import binomtest

    reference = binomtest(successes, total).proportion_ci(confidence_level=.95, method="wilson")
    assert rate(successes, total)["ci95"] == pytest.approx([reference.low, reference.high])


def test_bootstrap_does_not_publish_single_draw_interval():
    report = summarize([0, 1] * 10, [.2, .8] * 10, .7, 1)
    assert report["ci95"] is None
    assert report["interval_note"] is not None


def test_bootstrap_interval_with_sufficient_draws():
    report = summarize([0, 1] * 10, [i / 19 for i in range(20)], .7, 1100)
    assert report["bootstrap_valid"] >= 1000
    assert report["ci95"]["auroc"][0] < report["auroc"] < report["ci95"]["auroc"][1]
    assert report["interval_note"] is None


def test_perfect_separation_does_not_imply_zero_uncertainty():
    report = summarize([0, 1] * 10, [.2, .8] * 10, .7, 1100)
    assert report["ci95"]["auroc"] is None
    assert report["ci95"]["average_precision"] is None
    assert "degenerate" in report["interval_note"]


def test_paired_baseline_does_not_use_unmatched_patients(cohort):
    first = cohort["records"][0]
    second = deepcopy(first)
    second.update(patient_id="second", age_months=6)
    second["outcome"]["sepsis"] = 0
    second["baseline"] = {"value": 0}
    report = make_report([first, second], [[0, 0, 1], [1, 0, 0]], 20)
    assert report["overall"]["n"] == 2
    assert report["baseline"]["paired_n"] == 1
    assert report["baseline"]["rory_on_same_patients"]["n"] == 1
    assert report["baseline"]["recorded_screen"]["n"] == 1
    assert report["clinical_validation"] is False
    assert "not a sepsis probability" in report["calibration"]


def test_policy_matches_deployed_arithmetic(cohort):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend_a"))
    import torch
    from inference.predict import _risk_from_proba, _risk_to_recommendation

    for p in [[.4, .5, .1], [.1, .4, .5], [.45, .5, .05], [.3, 0, .7],
              [.65, 0, .35], [.29975, .0005, .69975]]:
        tensor = torch.tensor([p])
        expected = _risk_to_recommendation(_risk_from_proba(tensor))
        report = make_report(cohort["records"], tensor.tolist(), 5)
        assert report["recommendations"] == {expected: 1}


@pytest.fixture
def manifest_files(tmp_path, monkeypatch):
    from backend_a.validation import retrospective

    monkeypatch.setattr(retrospective, "BACKEND", tmp_path)
    monkeypatch.setattr(retrospective, "ROOT", tmp_path)
    for name in ("models/weights/train_stats.json", "inference/predict.py", "snapshot/vocab.txt",
                 "decision_policy.py"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    asset = tmp_path / "weights.bin"
    asset.write_bytes(b"original")
    return {
        "checkpoint": str(asset), "snapshot": str(tmp_path / "snapshot"),
        "snapshot_files": ["vocab.txt"], "spec": {"development_files": []},
        "development_files": [],
        "assets": {str(p): sha256(p) for p in tmp_path.rglob("*") if p.is_file()},
        "environment": {}, "python": sys.version,
        "policy": retrospective.POLICY.copy(),
    }


def test_manifest_detects_modified_asset(manifest_files):
    verify_manifest(manifest_files)
    asset = Path(manifest_files["checkpoint"])
    asset.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Frozen asset"):
        verify_manifest(manifest_files)


def test_manifest_requires_shared_decision_policy(manifest_files):
    policy = Path(manifest_files["checkpoint"]).parent / "decision_policy.py"
    del manifest_files["assets"][str(policy)]
    with pytest.raises(ValueError, match="not covered"):
        verify_manifest(manifest_files)


def test_manifest_rejects_new_tokenizer_configuration(manifest_files):
    snapshot = Path(manifest_files["snapshot"])
    verify_manifest(manifest_files)
    (snapshot / "tokenizer_config.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        verify_manifest(manifest_files)


def test_manifest_binds_actual_checkpoint(manifest_files, tmp_path):
    replacement = tmp_path / "other.bin"
    replacement.write_bytes(b"unfrozen")
    manifest_files["checkpoint"] = str(replacement)
    with pytest.raises(ValueError, match="not covered"):
        verify_manifest(manifest_files)


def test_snapshot_symlink_cannot_redirect_to_another_hashed_file(manifest_files, tmp_path):
    first, second = tmp_path / "first.txt", tmp_path / "second.txt"
    first.write_text("fixture")
    second.write_text("different")
    link = Path(manifest_files["snapshot"]) / "vocab.txt"
    link.unlink()
    link.symlink_to(first)
    manifest_files["assets"].update({str(p): sha256(p) for p in (first, second)})
    verify_manifest(manifest_files)
    link.unlink()
    link.symlink_to(second)
    with pytest.raises(ValueError, match="Frozen asset"):
        verify_manifest(manifest_files)


def test_freeze_hashes_consumed_symlink_path(manifest_files, tmp_path):
    snapshot = Path(manifest_files["snapshot"])
    (snapshot / "config.json").write_text("{}")
    target = tmp_path / "bert.bin"
    target.write_bytes(b"base-model fixture")
    link = snapshot / "pytorch_model.bin"
    link.symlink_to(target)
    (tmp_path / "models/weights/best_model.pt").write_bytes(b"checkpoint fixture")
    (tmp_path / "development.json").write_text('[{"patient_id": "development-fixture"}]')
    spec = tmp_path / "study.json"
    write_json(spec, {
        "endpoint_definition": "test fixture", "reference_standard": "test fixture",
        "setting": "pediatric_ed", "horizon_hours": 24,
        "development_files": ["development.json"], "development_sites": [],
        "development_end": None, "cohort_role": "exploratory",
        "baseline_name": None, "clinical_review_status": "pending",
    })
    output = tmp_path / "frozen.json"
    freeze(spec, snapshot, output)
    actual = json.loads(output.read_text())
    assert str(link) in actual["assets"]
    assert actual["assets"][str(link)] == sha256(target)
    verify_manifest(actual)


def test_json_digest_matches_parsed_bytes(tmp_path):
    path = tmp_path / "cohort.json"
    path.write_text('{"version": 1}')
    parsed, digest = read_json_hashed(path)
    assert parsed["version"] == 1
    assert digest == sha256(path)
    path.write_text('{"version": 2}')
    assert digest != sha256(path)


def test_outputs_cannot_silently_overwrite(tmp_path):
    path = tmp_path / "report.json"
    write_json(path, {"clinical_validation": False})
    with pytest.raises(FileExistsError):
        write_json(path, {"clinical_validation": True})
    assert json.loads(path.read_text())["clinical_validation"] is False
