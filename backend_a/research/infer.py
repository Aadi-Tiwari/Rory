"""Produce local frozen-model predictions and their provenance manifest."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform

from decision_policy import POLICY_VERSION, synthetic_label
from research.audit import LATER_INFORMATION, VITAL_UNITS, file_hash, read_json
from research.evaluate import validate_rows


def case_record(case, data_kind):
    return {"case_id": case["patient_id"], "label": synthetic_label(case["ground_truth"]) if data_kind == "synthetic" else case["label"],
            "age_months": case["age_months"], "sex": case.get("sex", "unknown"),
            "missing_vitals": sum(case["vitals"].get(key) is None for key in VITAL_UNITS)}


def predict_dataset(dataset, checkpoint, data_kind, allow_legacy=False):
    if not checkpoint.is_file():
        raise FileNotFoundError("A trusted trained checkpoint is required; no predictions were generated")
    cases, dataset_hash = read_json(dataset)
    checkpoint_hash = file_hash(checkpoint)
    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset must contain cases")
    later = sum(bool(LATER_INFORMATION.search(case["complaint_text"])) for case in cases)
    if later and not (data_kind == "synthetic" and allow_legacy):
        raise ValueError("Possible post-arrival information in complaints. Resolve timing before inference; legacy synthetic reproduction needs --allow-legacy-synthetic")
    rows = [case_record(case, data_kind) for case in cases]
    validate_rows(rows, require_probabilities=False)
    import torch
    from models.checkpoint import load_model
    from models.text_encoder import MODEL_NAME, MODEL_REVISION

    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model = load_model(checkpoint)
    with torch.inference_mode():
        for case, row in zip(cases, rows):
            row["probabilities"] = model([case["vitals"]], [case["complaint_text"]])["proba"][0].tolist()
    if file_hash(dataset) != dataset_hash or file_hash(checkpoint) != checkpoint_hash:
        raise ValueError("Input artifacts changed during inference")
    validate_rows(rows)
    return {"metadata": {"data_kind": data_kind, "dataset_sha256": dataset_hash, "checkpoint_sha256": checkpoint_hash,
                         "policy_version": POLICY_VERSION, "encoder_architecture": MODEL_NAME, "tokenizer_revision": MODEL_REVISION,
                         "encoder_construction_revision": MODEL_REVISION, "checkpoint_weight_origin": "Not established; checkpoint replaces all encoder weights",
                         "python": platform.python_version(), "packages": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "tokenizers", "numpy")},
                         "device": "cpu", "threads": 1, "seed": 0, "deterministic_algorithms": True,
                         "complaints_with_later_information": later, "reference_standard": "synthetic diagnosis mapping" if data_kind == "synthetic" else "operator-supplied labels; protocol review required",
                         "training_provenance": "Not established by this run", "scope": "Frozen model only; excludes drift, outlier, reasoning, and API confidence"}, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data-kind", choices=("synthetic", "real"), required=True)
    parser.add_argument("--allow-legacy-synthetic", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.dataset.resolve(), args.checkpoint.resolve()):
        parser.error("Output must not overwrite an input artifact")
    document = predict_dataset(args.dataset, args.checkpoint, args.data_kind, args.allow_legacy_synthetic)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "research_only", "rows": len(document["rows"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
