# inference/demo_cache.py
"""
Three hardcoded demo cases for the hackathon presentation.

Case 1 — obvious mimic     → HOME
Case 2 — ambiguous + drift → ED
Case 3 — Rory Staunton     → 911

Call get_demo_cases() to retrieve them as PredictRequest-compatible dicts.
Call run_demo() to run all three through predict() and print results.
"""

from __future__ import annotations

from inference.predict import predict

DEMO_CASES: list[dict] = [
    {
        "label":          "Obvious mimic — HOME",
        "patient_id":     "DEMO-001",
        "age_months":     36,
        "sex":            "F",
        "weight_kg":      14.5,
        "complaint_text": (
            "3-year-old female with 2-day runny nose and low-grade fever. "
            "Active and playful in waiting room. Eating and drinking normally. "
            "No respiratory distress. Cap refill brisk."
        ),
        "vitals": {
            "hr":           105,
            "rr":           24,
            "temp_f":       100.4,
            "spo2":         99,
            "cap_refill_s": 1.5,
        },
        "vitals_t30": {
            "hr":           100,
            "rr":           22,
            "temp_f":       100.1,
            "spo2":         99,
            "cap_refill_s": 1.4,
        },
    },
    {
        "label":          "Ambiguous + drift — ED",
        "patient_id":     "DEMO-002",
        "age_months":     18,
        "sex":            "M",
        "weight_kg":      11.0,
        "complaint_text": (
            "18-month-old male with mild fussiness and low-grade fever x2 days. "
            "Mom feels something is off but child was playing this morning. "
            "HR noted elevated at triage. On reassessment at 30 minutes: "
            "HR increased from 142 to 151 bpm, SpO2 drifting down from 97% to 95%."
        ),
        "vitals": {
            "hr":           142,
            "rr":           32,
            "temp_f":       101.2,
            "spo2":         97,
            "cap_refill_s": 2.4,
        },
        "vitals_t30": {
            "hr":           151,
            "rr":           34,
            "temp_f":       101.6,
            "spo2":         95,
            "cap_refill_s": 2.7,
        },
    },
    {
        "label":          "Rory Staunton — 911",
        "patient_id":     "RORY-2012-0330",
        "age_months":     144,
        "sex":            "M",
        "weight_kg":      45.0,
        "complaint_text": (
            "12-year-old male with 2-day history of fever, vomiting, and left leg pain. "
            "Sustained a minor laceration on leg during gym class 3 days ago. "
            "Mom reports he has been increasingly lethargic, refusing food, high fever at home. "
            "Father notes the child looks pale and 'just not right'. No rash. "
            "HR increased from 124 to 130 bpm between triage and first assessment. "
            "Cap refill 3 seconds and not improving."
        ),
        "vitals": {
            "hr":           130,
            "rr":           22,
            "temp_f":       104.7,
            "spo2":         98,
            "cap_refill_s": None,
        },
        "vitals_t30": {
            "hr":           136,
            "rr":           24,
            "temp_f":       104.9,
            "spo2":         97,
            "cap_refill_s": None,
        },
    },
]


def get_demo_cases() -> list[dict]:
    return DEMO_CASES


def run_demo() -> None:
    print("=" * 60)
    print("RORY — Demo Cases")
    print("=" * 60)

    for case in DEMO_CASES:
        print(f"\n{case['label']}")
        print("-" * 40)
        result = predict(
            patient_id=case["patient_id"],
            age_months=case["age_months"],
            sex=case["sex"],
            weight_kg=case["weight_kg"],
            complaint_text=case["complaint_text"],
            vitals_raw=case["vitals"],
            vitals_t30=case.get("vitals_t30"),
        )
        print(f"  recommendation : {result['recommendation']}")
        print(f"  risk           : {result['risk']}")
        print(f"  confidence     : {result['confidence']}")
        print(f"  completeness   : {result['completeness']}")
        print(f"  outlier_flag   : {result['outlier_flag']}")
        print(f"  drift_alert    : {result['drift_alert']}")
        print(f"  cluster_drift  : {result['cluster_drift']}")
        print(f"  trend          : {result['sepsis_confidence_trend']}")
        print(f"  reasoning:")
        for r in result["reasoning"][:3]:
            print(f"    [{r['weight']:.2f}] {r['bullet']}")

    print("\nDone.\n")


if __name__ == "__main__":
    run_demo()