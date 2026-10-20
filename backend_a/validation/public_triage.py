from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import math
from pathlib import Path

from backend_a.decision_policy import risk_from_probabilities
from backend_a.validation.retrospective import (
    POLICY, VITALS, freeze_assets, predict_probabilities, read_json_hashed, sha256,
    verify_manifest, write_json,
)

RELEASE_SHA256 = "36acddd0c4358affd4adc1170f46c10a43d4bd00704a46d4bca5e7dabb3f3e5c"
STUDY = {
    "name": "Nairobi admission association with missing text and capillary refill",
    "dataset": "https://doi.org/10.6084/m9.figshare.9104918.v1",
    "file": "https://ndownloader.figshare.com/files/16604291",
    "license": "CC BY 4.0",
    "source_study": "https://doi.org/10.12688/wellcomeopenres.15387.3",
    "endpoint": "Released admitted field: clinician-decided admission for at least 24 hours.",
    "encoding": "admitted 0 = no, 1 = yes; binary release encoding interpretation.",
    "eligibility": "Known binary admission, age 2 through 60 months inclusive, at least one numeric model vital.",
    "age": "years*12 + months + days/30; blank components zero unless all are blank.",
    "age_source": "https://github.com/pmwaniki/ppg-analysis/blob/8679a3a31d023f5e22b7d7c23404fa0bd222d474/EDA/descriptives.py",
    "inputs": "pulse_rate, resp_rate, temp converted C to F, oxygen_sat; cap_refill_s missing, complaint empty.",
    "timing": "Study-time measurements; some emergency measurements followed treatment initiation.",
    "thresholds": [0.35, 0.70],
    "score_policy": POLICY,
    "resamples": 2000,
    "seed": 42,
    "development_files": ["backend_a/data/hero_cohort.json", "backend_a/data/held_out.json"],
    "fitting": "None. No tuning, recalibration, imputation fitting, or narrative generation.",
    "clinical_validation": False,
    "clinical_review_status": "No new clinical endorsement claimed for this public-data association study.",
}


def number(value: str) -> float | None:
    if not value.strip():
        return None
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("Nonfinite source value.")
    return parsed


def prepare_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    records, exclusions, seen = [], Counter(), set()
    for index, row in enumerate(rows):
        fingerprint = tuple(sorted(row.items()))
        if fingerprint in seen:
            exclusions["exact_duplicate_row"] += 1
            continue
        seen.add(fingerprint)
        if row["admitted"] not in ("0", "1"):
            exclusions["missing_or_unknown_admission"] += 1
            continue
        components = [number(row[key]) for key in ("age_years", "age_mths", "age_days")]
        if all(value is None for value in components):
            exclusions["missing_age"] += 1
            continue
        if any(value is not None and value < 0 for value in components):
            raise ValueError("Negative age component.")
        years, months, days = [value or 0 for value in components]
        age = years * 12 + months + days / 30
        if not 2 <= age <= 60:
            exclusions["outside_age_range"] += 1
            continue
        vitals = {
            "hr": number(row["pulse_rate"]), "rr": number(row["resp_rate"]),
            "temp_f": number(row["temp"]), "spo2": number(row["oxygen_sat"]),
            "cap_refill_s": None,
        }
        if all(value is None for value in vitals.values()):
            exclusions["all_model_vitals_missing"] += 1
            continue
        if vitals["temp_f"] is not None:
            vitals["temp_f"] = vitals["temp_f"] * 9 / 5 + 32
        records.append({
            "source_row": index + 2,
            "age_months": age,
            "admitted": int(row["admitted"]),
            "resuscitation_code": row["data_resuscitation"] or "missing",
            "vitals": {key: None if value is None else {"value": value} for key, value in vitals.items()},
            "complaint": {"value": ""},
        })
    if not records:
        raise ValueError("No eligible records.")
    return records, {
        "released_rows": len(rows), "included_rows": len(records),
        "exclusions_in_applied_order": dict(exclusions),
        "unit": "Released participant row; original identifiers are not released.",
        "linkage_limit": "Exact duplicate rows are removed; repeated patients cannot be independently linked.",
    }


def read_cohort(path: Path) -> tuple[list[dict], dict, str]:
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != RELEASE_SHA256:
        raise ValueError("CSV differs from the inspected Figshare version.")
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    records, flow = prepare_rows(rows)
    return records, flow, digest


def freeze(snapshot: Path, source: Path, output: Path) -> None:
    _, flow, digest = read_cohort(source)
    manifest = freeze_assets(STUDY, snapshot)
    manifest.update({"source_sha256": digest, "participant_flow": flow})
    write_json(output, manifest)


def make_report(records: list[dict], probabilities: list[list[float]]) -> dict:
    import numpy as np
    from backend_a.validation.metrics import summarize

    proba = np.asarray(probabilities, dtype=np.float32)
    if (proba.shape != (len(records), 3) or not np.isfinite(proba).all()
            or not ((proba >= 0) & (proba <= 1)).all()
            or not np.allclose(proba.sum(axis=1), 1, atol=1e-6, rtol=0)):
        raise ValueError("Invalid class probabilities.")
    scores = np.array([risk_from_probabilities(row) for row in proba.tolist()])
    labels = [row["admitted"] for row in records]

    def subset(indices):
        if not indices:
            return {"n": 0}
        summary = summarize([labels[i] for i in indices], scores[indices].tolist(),
                            0.70, STUDY["resamples"], STUDY["seed"])
        summary["bootstrap_method"] = "Participant-row percentile bootstrap; linkage assumed from source study."
        summary["missing_vitals"] = {
            key: sum(records[i]["vitals"][key] is None for i in indices) for key in VITALS
        }
        return summary

    indices = list(range(len(records)))
    overall = subset(indices)
    lower = summarize(labels, scores.tolist(), 0.35, STUDY["resamples"], STUDY["seed"])
    lower["bootstrap_method"] = overall["bootstrap_method"]
    return {
        "study": STUDY,
        "clinical_validation": False,
        "interpretation": "Association of frozen urgency scores with admission under missing-input ablation.",
        "sepsis_calibration": "Not estimable: no sepsis labels and urgency is not a sepsis probability.",
        "external_validation": "Not established for the intended text-and-vitals workflow or sepsis endpoint.",
        "baseline": "Unavailable: no verified recorded screening result or complete score coding.",
        "overall_at_070": overall,
        "overall_at_035": lower,
        "score_quantiles": dict(zip(("min", "q25", "median", "q75", "max"),
                                    np.quantile(scores, [0, .25, .5, .75, 1]).tolist())),
        "threshold_bands": dict(Counter(
            "below_035" if score < .35 else "035_to_070" if score < .70 else "at_least_070"
            for score in scores.tolist()
        )),
        "age_groups_months_at_070": {
            name: subset([i for i, row in enumerate(records) if low <= row["age_months"] < high])
            for name, low, high in (("[2,12)", 2, 12), ("[12,24)", 12, 24),
                                    ("[24,60]", 24, math.nextafter(60, math.inf)))
        },
        "resuscitation_codes_at_070": {
            code: subset([i for i, row in enumerate(records) if row["resuscitation_code"] == code])
            for code in sorted({row["resuscitation_code"] for row in records})
        },
        "resuscitation_coding_limit": "Raw codes only. No verified codebook to identify pre-treatment records.",
        "limitations": [
            "Empty narrative and missing numeric capillary refill differ from the intended workflow.",
            "Admission reflects local practice; it is neither sepsis nor the correct HOME / ED / 911 disposition.",
            "Study-time measurements can follow treatment; availability at initial triage cannot be established.",
            "Released rows differ from published article counts; selection is reported without forcing agreement.",
            "Intervals assume independent participant rows; absent identifiers prevent verifying linkage.",
            "Declared development files contain synthetic or illustrative cases; complete training history is not independently audited.",
            "Age component semantics are supported by author analysis of the same cohort, not a release-specific dictionary.",
            "No independent hospital replication, calibrated sepsis model, or clinical endorsement is established.",
        ],
        "missingness_by_admission": {
            str(label): {key: sum(row["vitals"][key] is None for row in records if row["admitted"] == label)
                         for key in VITALS}
            for label in (0, 1)
        },
    }


def run(manifest_path: Path, source: Path, output: Path, predictions: Path) -> None:
    from backend_a.validation.retrospective import ROOT

    if output.resolve() == predictions.resolve():
        raise ValueError("Report and participant predictions need distinct output paths.")
    if not predictions.resolve().is_relative_to((ROOT / "validation_private").resolve()):
        raise ValueError("Participant predictions must stay inside validation_private.")
    if output.exists() or predictions.exists():
        raise FileExistsError("Use new output paths; existing evidence is not overwritten.")
    manifest, manifest_digest = read_json_hashed(manifest_path)
    if manifest["spec"] != STUDY or manifest["source_sha256"] != RELEASE_SHA256:
        raise ValueError("Frozen study differs from the specified public benchmark.")
    verify_manifest(manifest)
    records, flow, cohort_digest = read_cohort(source)
    if flow != manifest["participant_flow"]:
        raise ValueError("Cohort selection changed after freezing.")
    print(f"Scoring {len(records)} public participant rows offline.", flush=True)
    probabilities = predict_probabilities(records, manifest)
    report = make_report(records, probabilities)
    verify_manifest(manifest)
    if sha256(source) != cohort_digest or sha256(manifest_path) != manifest_digest:
        raise ValueError("Study inputs changed during inference.")
    report.update({
        "participant_flow": flow, "source_sha256": cohort_digest,
        "manifest_sha256": manifest_digest, "checkpoint_sha256": manifest["assets"][manifest["checkpoint"]],
        "frozen_at": manifest["created_at"], "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    write_json(predictions, {
        "manifest_sha256": manifest_digest, "source_sha256": cohort_digest,
        "predictions": [{"source_row": row["source_row"], "probabilities": proba}
                        for row, proba in zip(records, probabilities)],
    })
    report["predictions_sha256"] = sha256(predictions)
    write_json(output, report)


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    freezing = commands.add_parser("freeze")
    freezing.add_argument("--snapshot", type=Path, required=True)
    freezing.add_argument("--source", type=Path, required=True)
    freezing.add_argument("--output", type=Path, required=True)
    running = commands.add_parser("run")
    running.add_argument("--manifest", type=Path, required=True)
    running.add_argument("--source", type=Path, required=True)
    running.add_argument("--output", type=Path, required=True)
    running.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.snapshot, args.source, args.output)
    else:
        run(args.manifest, args.source, args.output, args.predictions)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
