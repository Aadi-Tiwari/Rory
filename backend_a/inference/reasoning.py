# inference/reasoning.py
"""
Generates List[Reasoning] bullets from vitals + model risk score.
Rule-based attribution — no gradient computation needed at inference time.
Each bullet has a weight (0–1) and source_field so the frontend
can render a ranked explanation of the model's decision.
"""

from __future__ import annotations

from typing import Optional


# Age-band normal HR upper limits (PECARN)
_HR_UPPER: list[tuple[int, int, int]] = [
    (0,   3,   180),
    (3,   12,  170),
    (12,  36,  150),
    (36,  72,  140),
    (72,  144, 130),
    (144, 216, 120),
]

def _hr_upper(age_months: int) -> int:
    for lo, hi, limit in _HR_UPPER:
        if lo <= age_months < hi:
            return limit
    return 110


def _age_desc(age_months: int) -> str:
    if age_months < 12:
        return f"{age_months}mo infant"
    years = age_months // 12
    return f"{years}yo"


def generate_reasoning(
    age_months: int,
    vitals: dict,
    vitals_t30: Optional[dict],
    risk: float,
    complaint_text: str,
) -> list[dict]:
    """
    Returns a list of dicts matching the Reasoning schema:
        {"bullet": str, "weight": float, "source_field": str}

    Weight reflects how strongly this feature contributed to elevated risk.
    Bullets are ordered by weight descending before return.
    """
    bullets = []
    hr_limit = _hr_upper(age_months)
    desc     = _age_desc(age_months)

    hr  = vitals.get("hr")
    rr  = vitals.get("rr")
    t   = vitals.get("temp_f")
    sp  = vitals.get("spo2")
    cap = vitals.get("cap_refill_s")

    # ── HR ────────────────────────────────────────────────────────────────────
    if hr is not None:
        excess = hr - hr_limit
        if excess >= 30:
            bullets.append({
                "bullet":       f"HR {hr} bpm is {excess} bpm above the {desc} upper limit of {hr_limit}",
                "weight":       min(1.0, round(0.5 + excess / 100, 3)),
                "source_field": "vitals.hr",
            })
        elif excess >= 10:
            bullets.append({
                "bullet":       f"HR {hr} bpm mildly elevated for {desc} (limit {hr_limit})",
                "weight":       round(0.3 + excess / 200, 3),
                "source_field": "vitals.hr",
            })

    # ── SpO2 ──────────────────────────────────────────────────────────────────
    if sp is not None:
        if sp < 92:
            bullets.append({
                "bullet":       f"SpO2 {sp}% — critically low, below 92% threshold",
                "weight":       min(1.0, round(0.9 + (92 - sp) * 0.02, 3)),
                "source_field": "vitals.spo2",
            })
        elif sp < 95:
            bullets.append({
                "bullet":       f"SpO2 {sp}% — borderline, approaching concerning range",
                "weight":       round(0.5 + (95 - sp) * 0.08, 3),
                "source_field": "vitals.spo2",
            })

    # ── Cap refill ────────────────────────────────────────────────────────────
    if cap is not None:
        if cap >= 3.0:
            bullets.append({
                "bullet":       f"Cap refill {cap}s — prolonged (normal <2s), consistent with poor perfusion",
                "weight":       min(1.0, round(0.6 + (cap - 3.0) * 0.15, 3)),
                "source_field": "vitals.cap_refill_s",
            })
        elif cap >= 2.0:
            bullets.append({
                "bullet":       f"Cap refill {cap}s — borderline, warrants monitoring",
                "weight":       round(0.3 + (cap - 2.0) * 0.2, 3),
                "source_field": "vitals.cap_refill_s",
            })

    # ── Temp ──────────────────────────────────────────────────────────────────
    if t is not None:
        if t >= 104.0:
            bullets.append({
                "bullet":       f"Temperature {t}°F — high fever, systemic inflammatory response",
                "weight":       round(0.4 + (t - 104.0) * 0.05, 3),
                "source_field": "vitals.temp_f",
            })
        elif t < 97.0:
            bullets.append({
                "bullet":       f"Temperature {t}°F — hypothermia, atypical sepsis presentation",
                "weight":       0.65,
                "source_field": "vitals.temp_f",
            })

    # ── RR ────────────────────────────────────────────────────────────────────
    if rr is not None and rr >= 30:
        bullets.append({
            "bullet":       f"RR {rr} br/min — tachypneic, possible compensatory respiratory response",
            "weight":       min(1.0, round(0.35 + (rr - 30) * 0.02, 3)),
            "source_field": "vitals.rr",
        })

    # ── T+30 trajectory ───────────────────────────────────────────────────────
    if vitals_t30:
        hr2  = vitals_t30.get("hr")
        sp2  = vitals_t30.get("spo2")
        cap2 = vitals_t30.get("cap_refill_s")

        if hr and hr2 and hr2 > hr + 8:
            bullets.append({
                "bullet":       f"HR worsening trajectory: {hr} → {hr2} bpm over 30 minutes",
                "weight":       min(1.0, round(0.6 + (hr2 - hr) / 80, 3)),
                "source_field": "vitals_t30.hr",
            })
        if sp and sp2 and sp2 < sp - 2:
            bullets.append({
                "bullet":       f"SpO2 declining trajectory: {sp}% → {sp2}% over 30 minutes",
                "weight":       min(1.0, round(0.65 + (sp - sp2) * 0.04, 3)),
                "source_field": "vitals_t30.spo2",
            })
        if cap and cap2 and cap2 > cap + 0.4:
            bullets.append({
                "bullet":       f"Cap refill worsening: {cap}s → {cap2}s — perfusion declining",
                "weight":       min(1.0, round(0.55 + (cap2 - cap) * 0.1, 3)),
                "source_field": "vitals_t30.cap_refill_s",
            })

    # ── Complaint text signals ────────────────────────────────────────────────
    text_lower = complaint_text.lower()
    soft_flags = [
        ("lethargic",        0.55, "Complaint mentions lethargy — high-yield sepsis signal"),
        ("mottled",          0.75, "Complaint mentions mottling — strong perfusion concern"),
        ("not acting right", 0.50, "Parent reports child 'not acting right' — validated soft sepsis marker"),
        ("just not right",   0.50, "Parent reports child 'just not right' — validated soft sepsis marker"),
        ("something is off", 0.45, "Parent reports something is off — parental concern is clinically meaningful"),
        ("petechial",        0.80, "Complaint mentions petechial rash — meningococcemia must be excluded"),
        ("limp",             0.60, "Child described as limp — decreased tone, concerning for shock"),
        ("hypotherm",        0.65, "Hypothermia noted — atypical sepsis presentation"),
    ]
    for keyword, weight, desc_text in soft_flags:
        if keyword in text_lower:
            bullets.append({
                "bullet":       desc_text,
                "weight":       weight,
                "source_field": "complaint_text",
            })

    # ── Missing vitals penalty ────────────────────────────────────────────────
    missing = [k for k in ["hr", "rr", "temp_f", "spo2", "cap_refill_s"] if vitals.get(k) is None]
    if missing:
        bullets.append({
            "bullet":       f"{len(missing)} vital(s) missing at triage ({', '.join(missing)}) — incomplete picture",
            "weight":       round(0.1 * len(missing), 3),
            "source_field": "vitals.completeness",
        })

    # ── Overall risk summary ──────────────────────────────────────────────────
    if risk >= 0.85:
        bullets.append({
            "bullet":       f"Model risk score {risk:.2f} — high confidence sepsis pattern",
            "weight":       round(risk, 3),
            "source_field": "model.risk",
        })
    elif risk >= 0.5:
        bullets.append({
            "bullet":       f"Model risk score {risk:.2f} — elevated, pattern partially consistent with sepsis",
            "weight":       round(risk * 0.8, 3),
            "source_field": "model.risk",
        })

    bullets.sort(key=lambda b: b["weight"], reverse=True)
    return bullets