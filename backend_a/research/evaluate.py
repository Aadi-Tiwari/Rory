"""Evaluate frozen probabilities using the same decision policy as the service."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from statistics import NormalDist

from decision_policy import LABELS, POLICY_VERSION, recommendation_from_risk, risk_from_probabilities
from research.audit import file_hash, read_json


def proportion(successes, total):
    if total == 0:
        return {"numerator": successes, "denominator": total, "estimate": None, "wilson_95": None}
    p, z = successes / total, NormalDist().inv_cdf(0.975)
    center = (p + z * z / (2 * total)) / (1 + z * z / total)
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return {"numerator": successes, "denominator": total, "estimate": p,
            "wilson_95": [max(0.0, center - radius), min(1.0, center + radius)]}


def validate_rows(rows, require_probabilities=True):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Evaluation requires nonempty prediction rows")
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("label") not in LABELS:
            raise ValueError("Each row needs an explicit HOME, ED, or 911 reference label")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise ValueError("Case IDs must be nonempty and unique")
        ids.add(case_id)
        if require_probabilities:
            risk_from_probabilities(row.get("probabilities", []))
        age, missing = row.get("age_months"), row.get("missing_vitals")
        if type(age) is not int or not 0 <= age < 216:
            raise ValueError("age_months must be an integer in the pediatric research range [0, 216)")
        if type(missing) is not int or not 0 <= missing <= 5:
            raise ValueError("missing_vitals must be an integer from zero to five")


def metrics(rows):
    truth = [LABELS.index(row["label"]) for row in rows]
    predicted = [LABELS.index(recommendation_from_risk(risk_from_probabilities(row["probabilities"]))) for row in rows]
    matrix = [[0] * len(LABELS) for _ in LABELS]
    for actual, decision in zip(truth, predicted):
        matrix[actual][decision] += 1
    n = len(rows)
    classes = {}
    for i, label in enumerate(LABELS):
        tp = matrix[i][i]
        support, positives = sum(matrix[i]), sum(row[i] for row in matrix)
        fp, fn = positives - tp, support - tp
        classes[label] = {"support": support, "missed": fn, "false_alarms": fp,
                          "sensitivity": proportion(tp, support), "precision": proportion(tp, positives),
                          "specificity": proportion(n - support - fp, n - support)}
    calibration = {}
    for i, label in enumerate(LABELS):
        bins = []
        for bucket in range(10):
            indices = [j for j, row in enumerate(rows) if min(int(row["probabilities"][i] * 10), 9) == bucket]
            if indices:
                bins.append({"lower": bucket / 10, "upper": (bucket + 1) / 10, "n": len(indices),
                             "mean_probability": sum(rows[j]["probabilities"][i] for j in indices) / len(indices),
                             "observed_fraction": sum(truth[j] == i for j in indices) / len(indices)})
        calibration[label] = {"bins": bins, "ece": sum(b["n"] * abs(b["mean_probability"] - b["observed_fraction"]) for b in bins) / n}
    return {"n": n, "confusion_matrix": matrix, "class_order": list(LABELS), "per_class": classes,
            "accuracy": proportion(sum(a == p for a, p in zip(truth, predicted)), n),
            "undertriage": proportion(sum(p < a for a, p in zip(truth, predicted)), n),
            "overtriage": proportion(sum(p > a for a, p in zip(truth, predicted)), n),
            "multiclass_brier": sum(sum((p - (i == actual)) ** 2 for i, p in enumerate(row["probabilities"])) for actual, row in zip(truth, rows)) / n,
            "calibration": calibration,
            "constant_policy_baselines": {label: proportion(truth.count(i), n) for i, label in enumerate(LABELS)}}


def evaluate(document):
    rows, meta = document["rows"], document["metadata"]
    validate_rows(rows)
    if meta.get("policy_version") != POLICY_VERSION or meta.get("data_kind") not in ("synthetic", "real"):
        raise ValueError("Explicit data kind and matching frozen policy version are required")
    for key in ("dataset_sha256", "checkpoint_sha256"):
        value = meta.get(key, "")
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Missing artifact identity: " + key)
    groups = {
        "age_months": lambda row: "0-11" if row["age_months"] < 12 else "12-59" if row["age_months"] < 60 else "60-143" if row["age_months"] < 144 else "144-215",
        "missing_vitals": lambda row: "complete" if row["missing_vitals"] == 0 else "incomplete",
        "sex": lambda row: row.get("sex") if row.get("sex") in ("M", "F") else "unknown",
    }
    return {"status": "research_only", "clinical_validation": False, "metadata": meta, "overall": metrics(rows),
            "subgroups": {name: {group: metrics([row for row in rows if classify(row) == group]) for group in sorted({classify(row) for row in rows})} for name, classify in groups.items()},
            "limitations": ["Intervals assume independent unweighted cases. Repeated encounters and survey designs need another analysis.",
                            "Probability calibration is class-specific; the weighted risk and API confidence are not sepsis probabilities.",
                            "Small or absent subgroups cannot establish safety. No acceptance threshold has been clinically agreed.",
                            "Artifact hashes establish file identity, not provenance, licensing, or independence from training."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve() in (args.predictions.resolve(), args.dataset.resolve()):
        parser.error("Output must not overwrite an input artifact")
    document, prediction_hash = read_json(args.predictions)
    dataset, dataset_hash = read_json(args.dataset)
    if document["metadata"]["dataset_sha256"] != dataset_hash:
        raise ValueError("Dataset differs from the one used to produce predictions")
    report = evaluate(document)
    from research.infer import case_record

    ids = [row["patient_id"] for row in dataset]
    if Counter(ids) != Counter(row["case_id"] for row in document["rows"]):
        raise ValueError("Predictions must cover each dataset case exactly once")
    references = {case["patient_id"]: case_record(case, document["metadata"]["data_kind"]) for case in dataset}
    for row in document["rows"]:
        if any(row.get(key) != value for key, value in references[row["case_id"]].items()):
            raise ValueError("Prediction reference labels or subgroup values differ from the dataset")
    if prediction_hash != file_hash(args.predictions) or dataset_hash != file_hash(args.dataset):
        raise ValueError("Inputs changed during evaluation")
    report["predictions_sha256"] = prediction_hash
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "n": report["overall"]["n"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
