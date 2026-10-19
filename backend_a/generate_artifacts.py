"""Regenerate auxiliary artifacts from a recorded training split only."""

import argparse
import json
from pathlib import Path

from research.audit import file_hash, read_json


def training_cases(cohort, meta):
    ids = meta.get("train_patient_ids")
    validation = meta.get("validation_patient_ids")
    if not ids or not validation or len(set(ids)) != len(ids) or set(ids) & set(validation):
        raise ValueError("A disjoint, recorded training/validation split is required; legacy statistics cannot establish it")
    cases = {case["patient_id"]: case for case in cohort}
    if len(cases) != len(cohort) or set(ids) | set(validation) != set(cases):
        raise ValueError("Recorded split does not match the cohort")
    return [cases[case_id] for case_id in ids]


def collect_embeddings(model, cases):
    import numpy as np
    import torch

    embeddings, sepsis = [], []
    with torch.inference_mode():
        for case in cases:
            embedding = model([case["vitals"]], [case["complaint_text"]])["fused_emb"][0].numpy()
            embeddings.append(embedding)
            if case["ground_truth"] == "sepsis":
                sepsis.append(embedding)
    if not sepsis:
        raise ValueError("Training split has no sepsis examples for the legacy centroid")
    return np.array(embeddings), np.array(sepsis)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--train-stats", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    stats, stats_hash = read_json(args.train_stats)
    cohort, cohort_hash = read_json(args.cohort)
    checkpoint_hash = file_hash(args.checkpoint)
    meta = stats["meta"]
    if meta.get("cohort_sha256") != cohort_hash or meta.get("checkpoint_sha256") != checkpoint_hash:
        raise ValueError("Training manifest does not match the cohort and checkpoint")
    cases = training_cases(cohort, meta)
    outputs = [args.output_dir / name for name in ("dbscan.pkl", "sepsis_centroid.npy", "artifact_manifest.json")]
    if any(path.resolve() in {args.cohort.resolve(), args.checkpoint.resolve(), args.train_stats.resolve()} for path in outputs):
        parser.error("Outputs must not overwrite input artifacts")
    import torch
    from models.checkpoint import load_model
    from inference import dbscan_flag, cluster_drift

    torch.set_num_threads(1)
    if not meta.get("encoder_revision"):
        raise ValueError("A recorded encoder construction and tokenizer revision is required")
    embeddings, sepsis = collect_embeddings(load_model(args.checkpoint, meta["encoder_revision"]), cases)
    if (file_hash(args.cohort), file_hash(args.checkpoint), file_hash(args.train_stats)) != (cohort_hash, checkpoint_hash, stats_hash):
        raise ValueError("Inputs changed during artifact generation")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dbscan_flag.DBSCAN_PATH = args.output_dir / "dbscan.pkl"
    cluster_drift.CENTROID_PATH = args.output_dir / "sepsis_centroid.npy"
    dbscan_flag.fit(embeddings, eps=0.5, min_samples=5)
    cluster_drift.save_centroid(sepsis)
    manifest = {"cohort_sha256": cohort_hash, "checkpoint_sha256": checkpoint_hash,
                "train_stats_sha256": stats_hash, "training_cases": len(cases),
                "outputs": {path.name: file_hash(path) for path in (dbscan_flag.DBSCAN_PATH, cluster_drift.CENTROID_PATH)}}
    (args.output_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Auxiliary artifacts generated from the recorded training split. Research use only.")


if __name__ == "__main__":
    main()
