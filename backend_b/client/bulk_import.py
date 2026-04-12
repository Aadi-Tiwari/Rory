"""Bulk import seed_data.json into the Foundry Ontology via the Actions API.

Usage:
    cd C:/Users/tiwar/OneDrive/Documents/Projects/RORY/backend_b
    python -m client.bulk_import

Requires .env with FOUNDRY_WORKSPACE_URL, FOUNDRY_TOKEN, FOUNDRY_ONTOLOGY_RID.

This script uses the Foundry v2 Actions API to create objects via the
auto-generated Create actions. Key behaviors:

- Parameter names are camelCase (ageMonths, weightKg, etc.)
- Primary key fields (mrn, encounter_id, ...) are NOT sent. Foundry
  auto-generates the PK, which means foreign key references to seed
  data ("P001", "E001") will point at objects that don't exist.
- Foreign key fields are still sent as-is, so the Ontology will have
  dangling references. This is acceptable for demo visual density.
- Fields that don't exist as action parameters (e.g. RoryTriageDecision
  .confidence was never added to the object type) are omitted.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_URL = os.getenv("FOUNDRY_WORKSPACE_URL", "").rstrip("/")
TOKEN = os.getenv("FOUNDRY_TOKEN", "")
ONTOLOGY_RID = os.getenv("FOUNDRY_ONTOLOGY_RID", "")

SEED_DATA_PATH = Path(__file__).parent.parent / "foundry" / "ontology" / "seed_data.json"

# Mapping from seed JSON key to action type + (seed_field -> action_param) map.
# Primary key fields are omitted - Foundry auto-assigns them.
# Fields not listed here are omitted from the payload.
IMPORTS: list[tuple[str, str, dict[str, str]]] = [
    (
        "patients",
        "create-rory-patient",
        {
            "age_months": "ageMonths",
            "sex": "sex",
            "weight_kg": "weightKg",
            "setting": "setting",
        },
    ),
    (
        "encounters",
        "create-rory-encounter",
        {
            "patient_mrn": "patientMrn",
            "complaint_text": "complaintText",
            "setting": "setting",
            "timestamp": "timestamp",
        },
    ),
    (
        "vital_snapshots",
        "create-rory-vital-snapshot",
        {
            "encounter_id": "encounterId",
            "hr": "hr",
            "rr": "rr",
            "temp_f": "tempF",
            "spo2": "spo2",
            "cap_refill_s": "capRefillS",
            "completeness": "completeness",
        },
    ),
    (
        "triage_decisions",
        "create-rory-triage-decision",
        {
            "encounter_id": "encounterId",
            "triage_class": "triageClass",
            "risk": "risk",
            # confidence intentionally omitted - not in action parameters
            "reasoning": "reasoning",
            "outlier_flag": "outlierFlag",
            "cluster_drift": "clusterDrift",
            "drift_alert": "driftAlert",
            "sepsis_confidence_trend": "sepsisConfidenceTrend",
            "model_version": "modelVersion",
        },
    ),
    (
        "regulations_checks",
        "create-rory-regulations-check",
        {
            "encounter_id": "encounterId",
            "vital_signs_recorded": "vitalSignsRecorded",
            "mental_status_assessed": "mentalStatusAssessed",
            "sepsis_screen_triggered": "sepsisScreenTriggered",
            "escalation_required": "escalationRequired",
            "re_presentation_flag": "rePresentationFlag",
            "wound_source_documented": "woundSourceDocumented",
            "physician_notified": "physicianNotified",
            "discharge_criteria_met": "dischargeCriteriaMet",
            "missing_items": "missingItems",
        },
    ),
    (
        "protocol_citations",
        "create-rory-protocol-citation",
        {
            "source": "source",
            "section": "section",
            "page": "page",
            "quote": "quote",
            "pdf_url": "pdfUrl",
        },
    ),
]


def headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def build_payload(obj: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """Translate a seed object into the action parameter shape."""
    payload: dict[str, Any] = {}
    for seed_key, action_param in mapping.items():
        if seed_key in obj and obj[seed_key] is not None:
            payload[action_param] = obj[seed_key]
    return payload


def apply_action(action_name: str, parameters: dict[str, Any]) -> httpx.Response:
    url = (
        f"{WORKSPACE_URL}/api/v2/ontologies/{ONTOLOGY_RID}"
        f"/actions/{action_name}/apply"
    )
    body = {"parameters": parameters}
    return httpx.post(url, headers=headers(), json=body, timeout=15.0)


def get_object_label(obj: dict[str, Any]) -> str:
    for key in (
        "mrn",
        "encounter_id",
        "snapshot_id",
        "decision_id",
        "check_id",
        "citation_id",
    ):
        if key in obj:
            return str(obj[key])
    return "?"


def main() -> None:
    if not WORKSPACE_URL or not TOKEN or not ONTOLOGY_RID:
        print("ERROR: missing env vars in .env")
        sys.exit(1)

    if not SEED_DATA_PATH.exists():
        print(f"ERROR: seed_data.json not found at {SEED_DATA_PATH}")
        sys.exit(1)

    seed_data = json.loads(SEED_DATA_PATH.read_text(encoding="utf-8"))

    total_success = 0
    total_failure = 0

    for seed_key, action_name, mapping in IMPORTS:
        objects = seed_data.get(seed_key, [])
        print(f"\n=== {action_name} ({len(objects)} objects) ===")
        if not objects:
            print("  (no seed data)")
            continue

        for obj in objects:
            label = get_object_label(obj)
            payload = build_payload(obj, mapping)
            try:
                resp = apply_action(action_name, payload)
                if resp.status_code < 400:
                    print(f"  OK  {label}")
                    total_success += 1
                else:
                    body = resp.text
                    if len(body) > 300:
                        body = body[:300] + "..."
                    print(f"  ERR {label}: {resp.status_code} {body}")
                    total_failure += 1
            except httpx.HTTPError as e:
                print(f"  ERR {label}: {type(e).__name__}: {e}")
                total_failure += 1

    print(f"\n=== Summary ===")
    print(f"  Success: {total_success}")
    print(f"  Failure: {total_failure}")
    if total_failure == 0 and total_success > 0:
        print("\n  All seed objects imported successfully.")
        print("  Refresh the Foundry Object Explorer to see them.")
        print("\n  Note: primary keys were auto-assigned by Foundry, so the")
        print("  foreign key references in seed_data (patient_mrn='P001',")
        print("  encounter_id='E001', etc.) are dangling. The individual")
        print("  objects exist but cross-object links won't resolve.")


if __name__ == "__main__":
    main()
