from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys

from backend_a.decision_policy import POLICY_VERSION, risk_from_probabilities

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend_a"
VITALS = ("hr", "rr", "temp_f", "spo2", "cap_refill_s")
PACKAGES = ("torch", "numpy", "scipy", "scikit-learn", "transformers", "tokenizers")
AGE_BANDS = ((0, 12), (12, 60), (60, 144), (144, 216))
POLICY = {
    "version": POLICY_VERSION,
    "score": "(0.5 * p_ED + p_911) / sum(probabilities)",
    "ed_threshold": 0.35, "alarm_threshold": 0.70,
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_hashed(path: Path):
    content = path.read_bytes()
    return json.loads(content), hashlib.sha256(content).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def timestamp(value: str) -> datetime:
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Timestamps must include a timezone.")
    return stamp


def freeze(spec_path: Path, snapshot: Path, output: Path) -> None:
    spec = read_json(spec_path)
    required = ("endpoint_definition", "reference_standard", "setting", "horizon_hours",
                "development_files", "development_sites", "development_end", "cohort_role",
                "baseline_name", "clinical_review_status")
    if any(key not in spec for key in required):
        raise ValueError(f"Study specification requires: {', '.join(required)}")
    if not spec["endpoint_definition"].strip() or not spec["reference_standard"].strip():
        raise ValueError("The endpoint and reference standard must be specified.")
    if spec["setting"] != "pediatric_ed" or spec["horizon_hours"] != 24:
        raise ValueError("This protocol covers incident sepsis within 24 hours in a pediatric ED.")
    if spec["cohort_role"] not in ("external", "temporal", "exploratory"):
        raise ValueError("Unknown cohort role.")
    if spec["clinical_review_status"] not in ("pending", "approved"):
        raise ValueError("Clinical review status must be pending or approved.")
    if spec["cohort_role"] == "temporal":
        timestamp(spec["development_end"])
        if not spec["development_sites"]:
            raise ValueError("Temporal evaluation needs known development sites.")
    if spec["cohort_role"] == "external" and not spec["development_sites"]:
        raise ValueError("External evaluation needs known development sites.")
    write_json(output, freeze_assets(spec, snapshot))


def freeze_assets(spec: dict, snapshot: Path) -> dict:
    snapshot = snapshot.resolve()
    for filename in ("config.json", "vocab.txt"):
        if not (snapshot / filename).is_file():
            raise ValueError(f"Local tokenizer/model snapshot is missing {filename}.")
    development = [(ROOT / path).resolve() for path in spec["development_files"]]
    if not development:
        raise ValueError("Development patient files are required.")
    for path in development:
        if not path.is_file():
            raise ValueError("A declared development patient file is missing.")
        if not read_json(path):
            raise ValueError("Development patient files must not be empty.")
    files = [
        BACKEND / "models/weights/best_model.pt",
        BACKEND / "models/weights/train_stats.json",
        BACKEND / "inference/predict.py",
        BACKEND / "decision_policy.py",
        *sorted((BACKEND / "models").glob("*.py")),
        *sorted((BACKEND / "validation").glob("*.py")),
        *sorted(snapshot.rglob("*")),
        *development,
    ]
    files = sorted({path.absolute() for path in files if path.is_file()})
    if not (BACKEND / "models/weights/best_model.pt").is_file():
        raise ValueError("The trained checkpoint is missing.")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec": spec, "snapshot": str(snapshot),
        "snapshot_files": sorted(str(path.relative_to(snapshot)) for path in snapshot.rglob("*") if path.is_file()),
        "checkpoint": str(BACKEND / "models/weights/best_model.pt"),
        "development_files": [str(path) for path in development],
        "policy": POLICY,
        "environment": {name: importlib.metadata.version(name) for name in PACKAGES},
        "python": sys.version,
        "assets": {str(path): sha256(path) for path in files},
    }
    return manifest


def verify_manifest(manifest: dict) -> None:
    snapshot = Path(manifest["snapshot"]).resolve()
    snapshot_files = sorted(path for path in snapshot.rglob("*") if path.is_file())
    current_files = sorted(str(path.relative_to(snapshot)) for path in snapshot_files)
    if current_files != manifest["snapshot_files"]:
        raise ValueError("The frozen tokenizer/model snapshot file inventory changed.")
    development = {str((ROOT / name).resolve()) for name in manifest["spec"]["development_files"]}
    if development != set(manifest["development_files"]):
        raise ValueError("Development paths differ from the frozen study specification.")
    required = [
        Path(manifest["checkpoint"]), *snapshot_files,
        *(Path(name) for name in development),
        BACKEND / "models/weights/train_stats.json", BACKEND / "inference/predict.py",
        BACKEND / "decision_policy.py",
        *sorted((BACKEND / "models").glob("*.py")),
        *sorted((BACKEND / "validation").glob("*.py")),
    ]
    if any(str(path.absolute()) not in manifest["assets"] for path in required):
        raise ValueError("An inference or development asset is not covered by the manifest.")
    for name, digest in manifest["assets"].items():
        path = Path(name)
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Frozen asset changed or is missing: {path.name}")
    for name, version in manifest["environment"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError(f"Frozen package version changed: {name}")
    if sys.version != manifest["python"]:
        raise ValueError("Frozen Python version changed.")
    if manifest["policy"] != POLICY:
        raise ValueError("The decision policy differs from the deployed thresholds.")


def available(feature: dict, index: datetime) -> None:
    observed = timestamp(feature["observed_at"])
    entered = timestamp(feature["available_at"])
    if observed > entered or entered > index:
        raise ValueError("Predictor was observed or available after the prediction time.")


def validate_cohort(cohort: dict, spec: dict, development_ids: set[str]) -> list[dict]:
    if cohort["dataset_kind"] != "real":
        raise ValueError("The retrospective study requires real records, not synthetic cases.")
    if cohort["setting"] != spec["setting"]:
        raise ValueError("The cohort setting does not match the study.")
    if cohort["reference_standard"] != spec["reference_standard"]:
        raise ValueError("The outcome reference standard does not match the frozen study.")
    if cohort["clinical_review_status"] != "approved" or spec["clinical_review_status"] != "approved":
        raise ValueError("Clinical review of the endpoint and cohort is still pending.")
    for key in ("dataset_id", "access_basis", "patient_linkage", "sampling_description"):
        if not isinstance(cohort[key], str) or not cohort[key].strip():
            raise ValueError(f"Missing cohort provenance: {key}")
    if cohort["calendar_time_preserved"] is not True and spec["cohort_role"] == "temporal":
        raise ValueError("Patient-shifted dates cannot establish a temporal cohort.")
    records = cohort["records"]
    if not records:
        raise ValueError("The cohort is empty.")
    seen = set()
    for row in records:
        patient = row["patient_id"]
        if not isinstance(patient, str) or not patient.strip():
            raise ValueError("A linked, pseudonymous patient ID is required.")
        if patient in seen or patient in development_ids:
            raise ValueError("Repeated patient or development/evaluation patient overlap.")
        seen.add(patient)
        if not row["encounter_id"] or not row["site_id"]:
            raise ValueError("Encounter and site identifiers are required.")
        age = row["age_months"]
        if type(age) not in (int, float) or not math.isfinite(age) or not 0 <= age < 216:
            raise ValueError("Age must be in months and within the pediatric study population.")
        index = timestamp(row["index_time"])
        if spec["cohort_role"] == "external" and row["site_id"] in spec["development_sites"]:
            raise ValueError("An external evaluation site was used in development.")
        if spec["cohort_role"] == "temporal":
            if row["site_id"] not in spec["development_sites"] or index <= timestamp(spec["development_end"]):
                raise ValueError("Temporal records must follow development at a known development site.")
        text = row["complaint"]
        if not isinstance(text["value"], str) or not text["value"].strip():
            raise ValueError("Initial complaint text is required for multimodal evaluation.")
        if text["origin"] != "recorded_at_care":
            raise ValueError("Complaint text must come from care, not generated or reconstructed notes.")
        available(text, index)
        if set(row["vitals"]) != set(VITALS):
            raise ValueError("Provide all five vital fields; use null for missing observations.")
        if all(feature is None for feature in row["vitals"].values()):
            raise ValueError("At least one vital must be observed.")
        for feature in row["vitals"].values():
            if feature is not None:
                if type(feature["value"]) not in (int, float) or not math.isfinite(feature["value"]):
                    raise ValueError("Vital values must be finite numbers or null.")
                available(feature, index)
        if row["units"] != {"hr": "bpm", "rr": "breaths/min", "temp_f": "degF",
                            "spo2": "percent", "cap_refill_s": "seconds"}:
            raise ValueError("Vital units do not match Rory's inputs.")
        end = index + timedelta(hours=spec["horizon_hours"])
        outcome = row["outcome"]
        if type(outcome["sepsis"]) is not int or outcome["sepsis"] not in (0, 1):
            raise ValueError("The sepsis outcome must be 0 or 1.")
        if outcome["prevalent_sepsis"] is not False:
            raise ValueError("Prevalent or unknown baseline sepsis is outside this incident study.")
        followup = timestamp(outcome["followup_end"])
        if outcome["ascertainment_complete"] is not True:
            raise ValueError("Outcome ascertainment is incomplete.")
        if outcome["sepsis"]:
            onset = timestamp(outcome["onset_time"])
            if not index < onset <= end:
                raise ValueError("Positive onset is outside the future outcome window.")
            if followup < onset:
                raise ValueError("Positive onset is after the documented follow-up.")
        else:
            if outcome["onset_time"] is not None:
                raise ValueError("Negative outcomes must not contain a positive onset.")
            if followup < end:
                raise ValueError("Negative outcome ascertainment does not cover the entire study window.")
        baseline = row["baseline"]
        if baseline is not None:
            if not spec["baseline_name"] or baseline["name"] != spec["baseline_name"]:
                raise ValueError("Baseline differs from the frozen study.")
            if type(baseline["value"]) is not int or baseline["value"] not in (0, 1):
                raise ValueError("The recorded baseline screen must be binary.")
            available(baseline, index)
    return records


def predict_probabilities(records: list[dict], manifest: dict) -> list[list[float]]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    sys.path.insert(0, str(BACKEND))
    import torch
    from models import text_encoder
    from models.fusion import FusionModel, RoryModel
    from models.vitals_mlp import VitalsMLP

    torch.set_num_threads(1)
    text_encoder.MODEL_NAME = manifest["snapshot"]
    model = RoryModel(VitalsMLP(hidden_dim=64, out_dim=128),
                      text_encoder.TextEncoder(out_dim=128, device="cpu"),
                      FusionModel(vitals_dim=128, text_dim=128, hidden_dim=256))
    checkpoint = torch.load(manifest["checkpoint"], map_location="cpu", weights_only=True, mmap=True)
    model.load_state_dict(checkpoint, strict=True)
    del checkpoint
    model.eval()
    predictions = []
    with torch.inference_mode():
        for row in records:
            vitals = {key: None if value is None else value["value"] for key, value in row["vitals"].items()}
            out = model([vitals], [row["complaint"]["value"]])
            predictions.append(out["proba"][0].tolist())
    return predictions


def make_report(records: list[dict], probabilities: list[list[float]], resamples: int) -> dict:
    from backend_a.validation.metrics import summarize

    if len(records) != len(probabilities):
        raise ValueError("Prediction count does not match cohort.")
    scores = []
    for proba in probabilities:
        if (len(proba) != 3 or any(not math.isfinite(p) or not 0 <= p <= 1 for p in proba)
                or not math.isclose(sum(proba), 1, abs_tol=1e-6)):
            raise ValueError("Invalid class probabilities.")
        scores.append(risk_from_probabilities(proba))
    labels = [row["outcome"]["sepsis"] for row in records]

    def subset(indices):
        return summarize([labels[i] for i in indices], [scores[i] for i in indices],
                         threshold=0.70, resamples=resamples)

    paired = [i for i, row in enumerate(records) if row["baseline"] is not None]
    report = {
        "interpretation": "Exploratory discrimination of incident sepsis by a frozen triage-urgency score.",
        "clinical_validation": False,
        "calibration": "Not estimated: the ordinal urgency score is not a sepsis probability.",
        "scope": "Single-index model score and deployed thresholds; excludes drift, reasoning, and disposition safety.",
        "overall": subset(range(len(records))),
        "recommendations": dict(Counter("911" if s >= 0.70 else "ED" if s >= 0.35 else "HOME" for s in scores)),
        "missing_vitals": {key: sum(row["vitals"][key] is None for row in records) for key in VITALS},
        "age_groups_months": {}, "sites": {},
        "baseline": {"status": "unavailable", "paired_n": 0},
    }
    for low, high in AGE_BANDS:
        indices = [i for i, row in enumerate(records) if low <= row["age_months"] < high]
        report["age_groups_months"][f"[{low},{high})"] = subset(indices) if indices else {"n": 0}
    for site in sorted({row["site_id"] for row in records}):
        report["sites"][site] = subset([i for i, row in enumerate(records) if row["site_id"] == site])
    if paired:
        report["baseline"] = {
            "status": "paired descriptive comparison; no superiority test",
            "paired_n": len(paired), "rory_on_same_patients": subset(paired),
            "recorded_screen": summarize(
                [labels[i] for i in paired], [records[i]["baseline"]["value"] for i in paired],
                threshold=0.5, resamples=resamples),
        }
    return report


def run(manifest_path: Path, cohort_path: Path, output: Path, resamples: int) -> None:
    manifest, manifest_digest = read_json_hashed(manifest_path)
    verify_manifest(manifest)
    development_ids = set()
    for name in manifest["development_files"]:
        patients, digest = read_json_hashed(Path(name))
        if digest != manifest["assets"][name]:
            raise ValueError("Development patient data changed while being read.")
        development_ids.update(row["patient_id"] for row in patients)
    cohort, cohort_digest = read_json_hashed(cohort_path)
    records = validate_cohort(cohort, manifest["spec"], development_ids)
    probabilities = predict_probabilities(records, manifest)
    report = make_report(records, probabilities, resamples)
    verify_manifest(manifest)
    if sha256(cohort_path) != cohort_digest or sha256(manifest_path) != manifest_digest:
        raise ValueError("Study inputs changed during inference.")
    report.update({
        "dataset_id": cohort["dataset_id"], "cohort_role": manifest["spec"]["cohort_role"],
        "endpoint_definition": manifest["spec"]["endpoint_definition"],
        "manifest_sha256": manifest_digest, "cohort_sha256": cohort_digest,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "provenance_limit": "Timestamp, linkage, sampling, and adjudication declarations require source audit.",
    })
    write_json(output, report)


def audit(output: Path) -> None:
    paths = [BACKEND / "data/hero_cohort.json", BACKEND / "data/held_out.json"]
    development, held = [read_json(path) for path in paths]
    report = {"clinical_validation": False, "cohorts": {}}
    for path, records in zip(paths, (development, held)):
        report["cohorts"][path.name] = {
            "n": len(records), "sha256": sha256(path),
            "sources": dict(Counter(row.get("source", "unspecified") for row in records)),
            "labels": dict(Counter(row["ground_truth"] for row in records)),
            "text_mentions_reassessment": sum("reassessment" in row["complaint_text"].lower() for row in records),
            "records_without_index_time": sum("index_time" not in row for row in records),
        }
    report["overlapping_patient_ids"] = len(
        {r["patient_id"] for r in development} & {r["patient_id"] for r in held})
    report["overlapping_exact_complaint_texts"] = len(
        {r["complaint_text"] for r in development} & {r["complaint_text"] for r in held})
    checkpoint = BACKEND / "models/weights/best_model.pt"
    report["checkpoint"] = {"present": checkpoint.is_file(),
                            "sha256": sha256(checkpoint) if checkpoint.is_file() else None}
    report["findings"] = [
        "Generated cases and literature-attributed vignettes are not an independently collected patient cohort.",
        "The generator appends label-dependent T+30 reassessment information to initial complaint text.",
        "The existing evaluator uses argmax; deployment uses ordinal-score thresholds.",
        "The model forward pass does not receive structured age, sex, or weight.",
        "Patient ID separation alone does not establish independent source data.",
    ]
    write_json(output, report)


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--output", type=Path, required=True)
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--spec", type=Path, required=True)
    freeze_parser.add_argument("--snapshot", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--manifest", type=Path, required=True)
    run_parser.add_argument("--cohort", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    try:
        if args.command == "audit":
            audit(args.output)
        elif args.command == "freeze":
            freeze(args.spec, args.snapshot, args.output)
        else:
            run(args.manifest, args.cohort, args.output, args.resamples)
    except (ValueError, KeyError, FileNotFoundError, FileExistsError) as error:
        parser.exit(2, f"Evaluation stopped: {error}\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
