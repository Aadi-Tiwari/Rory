"""Audit the legacy synthetic cohorts without importing model dependencies."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from decision_policy import SYNTHETIC_LABELS

VITAL_UNITS = {"hr": "beats/min", "rr": "breaths/min", "temp_f": "degF", "spo2": "percent", "cap_refill_s": "seconds"}
LATER_INFORMATION = re.compile(r"reassess|30\s*min|trajectory|drifting|worsening from|improved from", re.I)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def normalize(text):
    return re.sub(r"\d+(?:\.\d+)?", "#", " ".join(text.lower().split()))


def audit(train, test):
    cohorts = {}
    for name, rows in (("training", train), ("evaluation", test)):
        if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Each cohort must be a nonempty list of case objects")
        ids = [row.get("patient_id") for row in rows]
        cohorts[name] = {
            "rows": len(rows), "duplicate_ids": sum(n - 1 for n in Counter(ids).values() if n > 1),
            "missing_ids": sum(not isinstance(value, str) or not value.strip() for value in ids),
            "unknown_diagnosis_labels": sum(row.get("ground_truth") not in SYNTHETIC_LABELS for row in rows),
            "complaints_with_later_information": sum(bool(LATER_INFORMATION.search(str(row.get("complaint_text", "")))) for row in rows),
            "source_labels": dict(Counter(str(row.get("source", "missing")) for row in rows)),
            "missing_vitals": {key: sum(row.get("vitals", {}).get(key) is None for row in rows) for key in VITAL_UNITS},
        }
    train_ids = {row.get("patient_id") for row in train if row.get("patient_id")}
    train_text = {row.get("complaint_text", "").strip().lower() for row in train}
    train_templates = {normalize(row.get("complaint_text", "")) for row in train}
    overlap = {
        "patient_ids": sum(row.get("patient_id") in train_ids for row in test),
        "exact_complaints": sum(row.get("complaint_text", "").strip().lower() in train_text for row in test),
        "numeric_normalized_complaints": sum(normalize(row.get("complaint_text", "")) in train_templates for row in test),
    }
    return {"scope": "Legacy synthetic cohort audit; not a clinical validation report", "cohorts": cohorts,
            "overlap": overlap, "expected_units": VITAL_UNITS,
            "arrival_evaluation_ready": False,
            "limitations": ["Diagnosis-derived labels are not clinical disposition reference labels.",
                            "Text screening flags possible temporal leakage; manual timestamp review is required.",
                            "Source strings and nonoverlapping IDs do not prove provenance or independence."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.train.resolve(), args.test.resolve()):
        parser.error("Output must not overwrite an input artifact")
    train, train_hash = read_json(args.train)
    test, test_hash = read_json(args.test)
    identities = {"training": train_hash, "evaluation": test_hash}
    report = audit(train, test)
    if identities != {"training": file_hash(args.train), "evaluation": file_hash(args.test)}:
        raise ValueError("Cohorts changed during audit")
    report["input_sha256"] = identities
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
