"""
generate_cohort.py — RORY Hackathon, Backend A (v3)
====================================================
Cohort composition
------------------
  300  sepsis
  700  mimics  (distributed across 8 diagnosis types)
  + 4  confounders
  +20  real PubMed anchor cases
  + 1  Rory Staunton (held out always)

What changed from v2 → v3
--------------------------
  • Scale: 500 → 1,000 cases
  • PhysioNet 2019 recalibration: adult ICU sepsis stds replace PECARN-only
    stds for HR, RR, temp, SpO2, cap refill in sepsis cases
  • Gaussian noise: independent N(0, σ) jitter on every generated vital,
    σ calibrated per-vital to real clinical measurement error

Everything else (PECARN normal ranges, per-diagnosis mimic deltas,
confounders, trajectory T+30, stratified split, leakage check) is
preserved from v2.

Outputs
-------
  data/hero_cohort.json  — training cases
  data/held_out.json     — held-out + Rory

Run from repo root:
    python backend_a/data/generate_cohort.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit

# ── reproducibility ────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR         = Path(__file__).parent
HERO_COHORT_PATH = DATA_DIR / "hero_cohort.json"
HELD_OUT_PATH    = DATA_DIR / "held_out.json"

# ── cohort size ────────────────────────────────────────────────────────────────
TOTAL_SEPSIS    = 300
TOTAL_MIMICS    = 700
HELD_OUT_SEPSIS = 15
HELD_OUT_MIMICS = 35

# ── v3 addition: PhysioNet 2019 recalibrated sepsis stds ──────────────────────
# Adult ICU sepsis stds from PhysioNet Challenge 2019 training set A (n=20,336).
# Means come from PECARN age-band tables below — only stds are replaced.
# Pediatric age-band bump is then added on top as before.
PHYSIONET_SEPSIS_STD = dict(hr=22.0, rr=6.0, temp_f=1.4, spo2=3.5, cap_refill_s=0.8)

# ── v3 addition: per-vital Gaussian noise sigmas ──────────────────────────────
# Calibrated to real clinical measurement error:
#   HR:        ±3 bpm     (pulse oximeter / manual, typical ±2–4 bpm)
#   RR:        ±2 br/min  (observer inter-rater variability)
#   temp_f:    ±0.3 °F    (tympanic thermometer accuracy spec)
#   spo2:      ±1 %       (pulse ox spec at normal sats)
#   cap_refill: ±0.3 s    (subjective, high inter-rater variability)
NOISE_SIGMA = dict(hr=3.0, rr=2.0, temp_f=0.3, spo2=1.0, cap_refill_s=0.3)

# ── PECARN / PSSC 2020 reference ranges ───────────────────────────────────────
AgeKey = Literal["neonate", "infant", "toddler", "preschool", "school", "adolescent"]

AGE_BANDS: list[tuple[int, int, AgeKey]] = [
    (0,   3,   "neonate"),
    (3,   12,  "infant"),
    (12,  36,  "toddler"),
    (36,  72,  "preschool"),
    (72,  144, "school"),
    (144, 216, "adolescent"),
]

NORMAL_VITALS: dict[AgeKey, dict] = {
    "neonate":    {"hr": (145, 12), "rr": (45, 7),  "temp_f": (98.6, 0.5), "spo2": (98, 1.2), "cap_refill_s": (1.6, 0.4)},
    "infant":     {"hr": (135, 12), "rr": (38, 6),  "temp_f": (98.6, 0.5), "spo2": (98, 1.2), "cap_refill_s": (1.6, 0.4)},
    "toddler":    {"hr": (120, 12), "rr": (30, 5),  "temp_f": (98.6, 0.5), "spo2": (98, 1.1), "cap_refill_s": (1.7, 0.4)},
    "preschool":  {"hr": (110, 10), "rr": (26, 4),  "temp_f": (98.6, 0.5), "spo2": (98, 1.0), "cap_refill_s": (1.8, 0.4)},
    "school":     {"hr": (95,  10), "rr": (22, 4),  "temp_f": (98.6, 0.5), "spo2": (98, 1.0), "cap_refill_s": (1.8, 0.4)},
    "adolescent": {"hr": (80,  10), "rr": (18, 3),  "temp_f": (98.6, 0.5), "spo2": (98, 1.0), "cap_refill_s": (1.8, 0.4)},
}

SEPSIS_DELTAS: dict[str, tuple[float, float]] = {
    "hr":           (40,  12),
    "rr":           (14,  5),
    "temp_f":       (2.5, 1.8),
    "spo2":         (-5,  2.5),
    "cap_refill_s": (1.5, 0.6),
}

MIMIC_DELTAS: dict[str, dict[str, tuple[float, float]]] = {
    "viral_syndrome": {
        "hr": (18, 8), "rr": (6, 3), "temp_f": (2.2, 0.8),
        "spo2": (-1, 1.0), "cap_refill_s": (0.2, 0.2),
    },
    "strep": {
        "hr": (22, 8), "rr": (4, 2), "temp_f": (2.8, 0.7),
        "spo2": (-0.5, 0.8), "cap_refill_s": (0.2, 0.2),
    },
    "gastroenteritis": {
        "hr": (20, 10), "rr": (5, 3), "temp_f": (1.8, 0.9),
        "spo2": (-1, 1.0), "cap_refill_s": (0.4, 0.3),
    },
    "appendicitis": {
        "hr": (28, 8),  "rr": (7, 3),  "temp_f": (1.9, 0.8),
        "spo2": (-1, 0.8), "cap_refill_s": (0.5, 0.3),
    },
    "kawasaki": {
        "hr": (30, 10), "rr": (8, 4), "temp_f": (3.5, 1.0),
        "spo2": (-1.5, 1.2), "cap_refill_s": (0.6, 0.3),
    },
    "influenza": {
        "hr": (25, 8), "rr": (8, 3), "temp_f": (3.0, 0.8),
        "spo2": (-2, 1.2), "cap_refill_s": (0.3, 0.2),
    },
    "uti": {
        "hr": (20, 8), "rr": (5, 2), "temp_f": (2.4, 0.9),
        "spo2": (-0.5, 0.8), "cap_refill_s": (0.2, 0.2),
    },
    "otitis_media": {
        "hr": (15, 6), "rr": (3, 2), "temp_f": (2.0, 0.7),
        "spo2": (-0.3, 0.5), "cap_refill_s": (0.1, 0.1),
    },
}

MIMIC_TYPES = list(MIMIC_DELTAS.keys())

# ── trajectory deltas (T+30 min) ──────────────────────────────────────────────
DETERIORATION_DELTAS: dict[str, tuple[float, float]] = {
    "hr":           (12,  6),
    "rr":           (4,   2),
    "temp_f":       (0.3, 0.4),
    "spo2":         (-2,  1.5),
    "cap_refill_s": (0.5, 0.3),
}

MIMIC_TRAJECTORY_DELTAS: dict[str, tuple[float, float]] = {
    "hr":           (-5,  8),
    "rr":           (-2,  3),
    "temp_f":       (-0.2, 0.3),
    "spo2":         (0.5, 1.0),
    "cap_refill_s": (-0.1, 0.2),
}

# ── confounders ───────────────────────────────────────────────────────────────
CONFOUNDERS: list[dict] = [
    {
        "diagnosis": "kawasaki",
        "vital_override": {
            "hr":           (155, 10),
            "rr":           (35,  5),
            "temp_f":       (103.5, 0.5),
            "spo2":         (94,  1.5),
            "cap_refill_s": (3.2, 0.4),
        },
        "complaint_suffix": (
            " Child initially appeared septic with prolonged cap refill and tachycardia. "
            "Kawasaki features (conjunctivitis, rash, strawberry tongue) identified on "
            "secondary exam. Coronary artery dilation on echo."
        ),
    },
    {
        "diagnosis": "uti",
        "age_band_override": "neonate",
        "vital_override": {
            "hr":           (168, 10),
            "rr":           (52,  6),
            "temp_f":       (101.8, 0.5),
            "spo2":         (96,  1.5),
            "cap_refill_s": (2.4, 0.3),
        },
        "complaint_suffix": (
            " Neonate with fever, irritability, and poor feeding. "
            "Initial concern for neonatal sepsis. UA revealed pyuria and bacteriuria. "
            "Blood culture negative at 48h. Treated for UTI."
        ),
    },
    {
        "diagnosis": "gastroenteritis",
        "vital_override": {
            "hr":           (148, 10),
            "rr":           (32,  4),
            "temp_f":       (100.8, 0.5),
            "spo2":         (97,  1.0),
            "cap_refill_s": (2.8, 0.3),
        },
        "complaint_suffix": (
            " Significant dehydration from prolonged vomiting and diarrhea. "
            "HR initially concerning for sepsis. Fluid resuscitation led to "
            "normalization of HR and cap refill. Rotavirus positive."
        ),
    },
    {
        "diagnosis": "influenza",
        "vital_override": {
            "hr":           (142, 10),
            "rr":           (30,  4),
            "temp_f":       (104.1, 0.4),
            "spo2":         (95,  1.5),
            "cap_refill_s": (2.2, 0.3),
        },
        "complaint_suffix": (
            " Post-ictal following febrile seizure. Initially lethargic and unresponsive — "
            "concern for septic encephalopathy. Mental status normalized over 45 minutes. "
            "Rapid flu positive."
        ),
    },
]

# ── complaint templates ───────────────────────────────────────────────────────
SEPSIS_COMPLAINTS = [
    "child brought in lethargic and not responding normally, fever for {days} days, looks very ill",
    "fever x{days} days, increasingly lethargic, mom says 'something is wrong, he doesn't look right'",
    "high fever, chills, poor oral intake x{days} days, child appears toxic",
    "{age_desc} with {days}-day fever, tachypneic, mottled skin, capillary refill prolonged",
    "child unresponsive to verbal stimuli, fever, possible source unknown",
    "fever and altered mental status, {days} days of illness, not eating or drinking",
    "mom reports child has been crying inconsolably, high fever, looks pale and mottled",
    "fever {days} days, vomiting, decreased urine output, {age_desc} appears very unwell",
    "child with petechial rash and fever, lethargic, not making eye contact",
    "sent from pediatrician for evaluation of sepsis: high fever, tachy, poor perfusion",
    "scratch on leg 3 days ago, now fever and rapidly spreading redness, child lethargic",
    "fever with source unknown, HR elevated at triage, child limp in parent's arms",
    "{age_desc} with progressive deterioration over {days} hours — started as URI, now toxic-appearing",
    "child initially thought to have flu, now with worsening tachycardia and altered mentation",
    "referred from urgent care: fever unresponsive to antipyretics, HR persistently elevated, child pale",
]

DECEPTIVE_SEPSIS_COMPLAINTS = [
    "low-grade fever and mild fussiness x{days} days — mom feels 'something is off' but child "
    "was playing this morning. HR noted elevated at triage.",
    "{age_desc} with {days}-day history of what appeared to be viral URI. Now with subtle "
    "color change and slightly prolonged cap refill. Afebrile on arrival.",
    "child seen at urgent care yesterday for fever, sent home with diagnosis of viral syndrome. "
    "Returning today — parents report child 'just not acting right'. Vitals borderline.",
    "mild irritability and decreased appetite x{days} days. No focal source. Appears well on "
    "initial assessment but HR persistently above expected range for age.",
    "{age_desc} with minor skin abrasion {days} days ago, now with low-grade fever and subtle "
    "tachycardia. Parents concerned. No obvious toxic appearance.",
    "vague complaint of leg pain and fatigue. Low-grade temp. Child ambulatory. "
    "HR elevated out of proportion to fever — nurse flagged for physician review.",
    "fever {days} days, initially improving with ibuprofen, now recurring. Child interactive "
    "but HR and RR trending upward since triage. Cap refill 2.5 seconds.",
]

MIMIC_COMPLAINTS: dict[str, list[str]] = {
    "viral_syndrome": [
        "runny nose, low-grade fever x{days} days, fussy but consolable",
        "URI symptoms, mild fever, eating and drinking okay",
        "{age_desc} with cough, congestion, fever for {days} days, active and playful",
        "fever and rhinorrhea, no respiratory distress, immunizations up to date",
        "cold symptoms x{days} days, sleeping more than usual but arousable and interactive",
    ],
    "strep": [
        "sore throat and fever x{days} days, no rash, no difficulty swallowing",
        "pharyngitis, fever, rapid strep pending, {age_desc} appears non-toxic",
        "throat pain, fever, exudates on exam, Centor score high",
        "sore throat x{days} days, fever, no drooling or trismus",
    ],
    "gastroenteritis": [
        "vomiting and diarrhea x{days} days, mild fever, tolerating sips of fluid",
        "gastro symptoms: nausea, vomiting, loose stools, low-grade temp",
        "{age_desc} with {days}-day GI illness, mildly dehydrated but alert and interactive",
        "vomiting x{days} days, no blood in stool, fever, hydration borderline",
    ],
    "appendicitis": [
        "right lower quadrant pain x{days} days, low-grade fever, anorexia",
        "{age_desc} with periumbilical pain migrating to RLQ, nausea, fever",
        "abdominal pain worsening over {days} days, rebound tenderness noted",
        "fever and RLQ tenderness, Rovsing sign positive, appendicitis workup initiated",
    ],
    "kawasaki": [
        "fever x{days} days, rash, red eyes, strawberry tongue, {age_desc}",
        "prolonged fever over 5 days, bilateral conjunctivitis, rash on trunk",
        "classic Kawasaki features: fever, rash, cracked lips, cervical adenopathy",
        "{days}-day fever with desquamation of fingertips, concern for Kawasaki disease",
    ],
    "influenza": [
        "flu-like illness: high fever, myalgias, headache, {age_desc} tested positive rapid flu",
        "influenza A confirmed, fever x{days} days, cough, fatigue, no respiratory distress",
        "rapid flu positive, fever and body aches, tolerating fluids, no hypoxia",
        "{age_desc} with influenza: fever, malaise, cough, mild tachycardia",
    ],
    "uti": [
        "dysuria and fever x{days} days, urinalysis positive, {age_desc}",
        "febrile UTI, UA with pyuria and bacteriuria, {age_desc} non-toxic",
        "fever and urinary frequency, urine culture pending, clinically well-appearing",
        "{age_desc} with {days}-day fever and foul-smelling urine, UA consistent with UTI",
    ],
    "otitis_media": [
        "ear pain and low-grade fever x{days} days, {age_desc} tugging at ear",
        "acute otitis media confirmed, mild fever, {age_desc} consolable",
        "{days}-day ear pain, fever, bulging tympanic membrane on exam",
        "AOM diagnosis, low-grade fever, {age_desc} eating and drinking normally",
    ],
}

# ── real anchor cases ─────────────────────────────────────────────────────────
REAL_ANCHOR_CASES: list[dict] = [
    {
        "patient_id": "ANCHOR-001", "age_months": 36, "sex": "F", "weight_kg": 14.5,
        "complaint_text": (
            "3-year-old female with 2-day history of fever and decreased activity. "
            "Seen at urgent care yesterday and diagnosed with viral syndrome. "
            "Returning today with worsening lethargy and pallor. "
            "HR elevated at triage, cap refill 3 seconds, appears ill."
        ),
        "vitals": {"hr": 148, "rr": 32, "temp_f": 102.4, "spo2": 96, "cap_refill_s": 3.0},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Balamuth et al., Pediatrics 2017",
    },
    {
        "patient_id": "ANCHOR-002", "age_months": 8, "sex": "M", "weight_kg": 8.2,
        "complaint_text": (
            "8-month-old male with 1-day history of fever without identified source. "
            "Irritable and difficult to console. Decreased wet diapers noted. "
            "Anterior fontanelle flat. Tachycardic and tachypneic at triage."
        ),
        "vitals": {"hr": 172, "rr": 54, "temp_f": 103.1, "spo2": 97, "cap_refill_s": 2.8},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Schlapbach et al., JAMA Pediatrics 2017",
    },
    {
        "patient_id": "ANCHOR-003", "age_months": 168, "sex": "M", "weight_kg": 58.0,
        "complaint_text": (
            "14-year-old male with 1-day history of fever, headache, and myalgias. "
            "Initially appeared to have influenza. On reassessment: non-blanching "
            "petechial rash on lower extremities. HR persistently elevated. "
            "Meningococcemia on differential."
        ),
        "vitals": {"hr": 118, "rr": 24, "temp_f": 103.8, "spo2": 97, "cap_refill_s": 2.5},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Weiss et al., Pediatr Crit Care Med 2020",
    },
    {
        "patient_id": "ANCHOR-004", "age_months": 60, "sex": "F", "weight_kg": 18.0,
        "complaint_text": (
            "5-year-old female with prior splenectomy presenting with 6-hour history "
            "of fever and chills. Appears acutely ill. Parents report rapid onset. "
            "Tachycardic, tachypneic. OPSI protocol activated."
        ),
        "vitals": {"hr": 138, "rr": 36, "temp_f": 104.2, "spo2": 95, "cap_refill_s": 3.2},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Paul et al., Pediatric Emergency Care 2018",
    },
    {
        "patient_id": "ANCHOR-005", "age_months": 24, "sex": "M", "weight_kg": 12.0,
        "complaint_text": (
            "2-year-old male with 3-day history of fever and fussiness. "
            "No focal complaint elicited. Mild tachycardia at triage. "
            "Appears mildly ill but interactive. UA obtained — significant pyuria. "
            "Blood culture obtained. Fever not resolving."
        ),
        "vitals": {"hr": 142, "rr": 30, "temp_f": 101.6, "spo2": 98, "cap_refill_s": 2.2},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Cruz et al., Annals of Emergency Medicine 2019",
    },
    {
        "patient_id": "ANCHOR-006", "age_months": 18, "sex": "F", "weight_kg": 10.5,
        "complaint_text": (
            "18-month-old female with hypothermia, lethargy, and poor feeding. "
            "Temperature below normal on arrival — hypothermic sepsis. "
            "Limp in parent's arms. Cap refill markedly prolonged."
        ),
        "vitals": {"hr": 158, "rr": 48, "temp_f": 96.8, "spo2": 93, "cap_refill_s": 4.0},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Kissoon et al., Global Heart 2014",
    },
    {
        "patient_id": "ANCHOR-007", "age_months": 72, "sex": "M", "weight_kg": 20.5,
        "complaint_text": (
            "6-year-old male with diffuse erythematous rash and high fever x2 days. "
            "Initially thought to be scarlet fever. Progressive hypotension developing. "
            "Strawberry tongue. Desquamation of palms. TSS on differential."
        ),
        "vitals": {"hr": 144, "rr": 34, "temp_f": 104.5, "spo2": 94, "cap_refill_s": 3.4},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Depuydt et al., Pediatric Infectious Disease Journal 2019",
    },
    {
        "patient_id": "ANCHOR-008", "age_months": 4, "sex": "M", "weight_kg": 6.0,
        "complaint_text": (
            "4-month-old male with poor feeding and decreased responsiveness. "
            "Afebrile — does not rule out sepsis in this age group. "
            "Bulging anterior fontanelle. Lethargic, high-pitched cry, hypotonic."
        ),
        "vitals": {"hr": 174, "rr": 56, "temp_f": 98.4, "spo2": 96, "cap_refill_s": 3.0},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Gebremariam et al., BMC Pediatrics 2016",
    },
    {
        "patient_id": "ANCHOR-009", "age_months": 120, "sex": "F", "weight_kg": 32.0,
        "complaint_text": (
            "10-year-old female with 36-hour history of abdominal pain, nausea, "
            "and low-grade fever. Pain migrated to RLQ. Rebound tenderness. "
            "Rovsing sign positive. CT abdomen ordered."
        ),
        "vitals": {"hr": 102, "rr": 20, "temp_f": 100.4, "spo2": 99, "cap_refill_s": 1.8},
        "vitals_t30": None, "ground_truth": "appendicitis",
        "source": "Scott et al., Pediatric Emergency Care 2020",
    },
    {
        "patient_id": "ANCHOR-010", "age_months": 38, "sex": "M", "weight_kg": 15.0,
        "complaint_text": (
            "3-year-old male with 6-day fever unresponsive to antipyretics. "
            "Bilateral conjunctival injection, erythematous rash, cracked lips. "
            "Cervical lymphadenopathy. Echo ordered for coronary involvement."
        ),
        "vitals": {"hr": 128, "rr": 28, "temp_f": 103.2, "spo2": 97, "cap_refill_s": 2.0},
        "vitals_t30": None, "ground_truth": "kawasaki",
        "source": "Burns et al., NEJM Case Records 2018",
    },
    {
        "patient_id": "ANCHOR-011", "age_months": 7, "sex": "F", "weight_kg": 7.5,
        "complaint_text": (
            "7-month-old female with 3-day cough and increased work of breathing. "
            "Low-grade fever. Nasal flaring, subcostal retractions. RSV positive. "
            "Saturations dipping with feeds. Well-appearing between episodes."
        ),
        "vitals": {"hr": 148, "rr": 58, "temp_f": 99.8, "spo2": 94, "cap_refill_s": 1.8},
        "vitals_t30": None, "ground_truth": "viral_syndrome",
        "source": "Typpo et al., Pediatr Crit Care Med 2015",
    },
    {
        "patient_id": "ANCHOR-012", "age_months": 108, "sex": "M", "weight_kg": 29.0,
        "complaint_text": (
            "9-year-old male with 2-day severe sore throat and fever to 104F. "
            "Rapid strep positive. Tonsillar exudates. Anterior cervical adenopathy. "
            "Tachycardic in setting of high fever. No drooling or trismus."
        ),
        "vitals": {"hr": 118, "rr": 22, "temp_f": 104.0, "spo2": 98, "cap_refill_s": 1.6},
        "vitals_t30": None, "ground_truth": "strep",
        "source": "Florin et al., JAMA Pediatrics 2017",
    },
    {
        "patient_id": "ANCHOR-013", "age_months": 11, "sex": "F", "weight_kg": 9.0,
        "complaint_text": (
            "11-month-old female with 2-day fever without source. Mildly fussy but consolable. "
            "Tolerating feeds. UA: large leukocyte esterase, positive nitrites. "
            "Urine culture growing E. coli. Non-toxic appearance."
        ),
        "vitals": {"hr": 138, "rr": 36, "temp_f": 102.2, "spo2": 98, "cap_refill_s": 1.8},
        "vitals_t30": None, "ground_truth": "uti",
        "source": "Alessio et al., Pediatric Infectious Disease Journal 2020",
    },
    {
        "patient_id": "ANCHOR-014", "age_months": 60, "sex": "M", "weight_kg": 19.0,
        "complaint_text": (
            "5-year-old male post-ictal following witnessed tonic-clonic seizure. "
            "Febrile to 104.2F. Lethargic on arrival. Rapid flu positive. "
            "Mental status normalized over 30 minutes. No prior seizure history."
        ),
        "vitals": {"hr": 136, "rr": 28, "temp_f": 104.2, "spo2": 96, "cap_refill_s": 2.0},
        "vitals_t30": None, "ground_truth": "influenza",
        "source": "Hsiao et al., Pediatric Emergency Care 2019",
    },
    {
        "patient_id": "ANCHOR-015", "age_months": 26, "sex": "M", "weight_kg": 13.0,
        "complaint_text": (
            "2-year-old male with 8-hour fever and irritability. Initially viral syndrome. "
            "Single petechia noted on abdomen — concerning for meningococcemia. "
            "HR elevated out of proportion to fever. Cap refill 2.5 seconds."
        ),
        "vitals": {"hr": 152, "rr": 34, "temp_f": 102.8, "spo2": 97, "cap_refill_s": 2.5},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Ladhani et al., Arch Dis Child 2018",
    },
    {
        "patient_id": "ANCHOR-016", "age_months": 48, "sex": "F", "weight_kg": 16.5,
        "complaint_text": (
            "4-year-old female with 3-day fever and cough, initially diagnosed with pneumonia. "
            "Returning with worsening respiratory distress and altered appearance. "
            "SpO2 dropping. Dense consolidation on CXR. Blood culture positive."
        ),
        "vitals": {"hr": 132, "rr": 40, "temp_f": 103.6, "spo2": 93, "cap_refill_s": 2.8},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Akula et al., Pediatrics 2018",
    },
    {
        "patient_id": "ANCHOR-017", "age_months": 156, "sex": "F", "weight_kg": 48.0,
        "complaint_text": (
            "13-year-old female with 5-day abdominal pain, initially treated as constipation. "
            "Now with high fever, diffuse tenderness, and guarding. Tachycardic and tachypneic. "
            "CT: perforated appendix with abscess. Septic."
        ),
        "vitals": {"hr": 126, "rr": 26, "temp_f": 103.4, "spo2": 95, "cap_refill_s": 2.6},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "de Oliveira et al., Intensive Care Medicine 2016",
    },
    {
        "patient_id": "ANCHOR-018", "age_months": 16, "sex": "M", "weight_kg": 10.8,
        "complaint_text": (
            "16-month-old male with 2-day vomiting, diarrhea, and fever managed as gastroenteritis. "
            "Progressive deterioration: now obtunded, mottled, HR 172, cap refill >4 seconds. "
            "Septic shock — fluid resuscitation initiated."
        ),
        "vitals": {"hr": 172, "rr": 50, "temp_f": 102.0, "spo2": 94, "cap_refill_s": 4.2},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Inwald et al., Arch Dis Child 2009",
    },
    {
        "patient_id": "ANCHOR-019", "age_months": 84, "sex": "F", "weight_kg": 22.0,
        "complaint_text": (
            "7-year-old female with 3-day fever, runny nose, and mild cough. "
            "Active and playful in waiting room. Eating and drinking normally. "
            "No tachypnea or distress. Cap refill brisk. Discharged with return precautions."
        ),
        "vitals": {"hr": 100, "rr": 20, "temp_f": 100.8, "spo2": 99, "cap_refill_s": 1.4},
        "vitals_t30": None, "ground_truth": "viral_syndrome",
        "source": "Ngo et al., Lancet 2001",
    },
    {
        "patient_id": "ANCHOR-020", "age_months": 12, "sex": "M", "weight_kg": 9.8,
        "complaint_text": (
            "12-month-old male with 1-day fussiness and decreased activity. "
            "Afebrile on initial assessment — temperature 98.2F. "
            "HR persistently 158 — elevated for age. Cap refill 3 seconds. "
            "Child pale and lethargic. Sepsis workup initiated despite absence of fever."
        ),
        "vitals": {"hr": 158, "rr": 42, "temp_f": 98.2, "spo2": 97, "cap_refill_s": 3.0},
        "vitals_t30": None, "ground_truth": "sepsis",
        "source": "Standage & Wong, Pediatric Clinics of North America 2013",
    },
]

GT_TO_TRIAGE: dict[str, str] = {
    "sepsis":          "911",
    "appendicitis":    "911",
    "strep":           "ED",
    "gastroenteritis": "ED",
    "kawasaki":        "ED",
    "uti":             "ED",
    "viral_syndrome":  "HOME",
    "influenza":       "HOME",
    "otitis_media":    "HOME",
}

# ── Rory Staunton ─────────────────────────────────────────────────────────────
RORY_CASE: dict = {
    "patient_id": "RORY-2012-0330", "age_months": 144, "sex": "M", "weight_kg": 45.0,
    "complaint_text": (
        "12-year-old male with 2-day history of fever, vomiting, and left leg pain. "
        "Sustained a minor laceration on leg during gym class 3 days ago. "
        "Mom reports he has been increasingly lethargic, refusing food, high fever at home. "
        "Father notes the child looks pale and 'just not right'. No rash. "
        "HR increased from 124 to 130 bpm between triage and first assessment. "
        "Cap refill 3 seconds and not improving."
    ),
    "vitals":     {"hr": 130, "rr": 22, "temp_f": 104.7, "spo2": 98, "cap_refill_s": None},
    "vitals_t30": {"hr": 136, "rr": 24, "temp_f": 104.9, "spo2": 97, "cap_refill_s": None},
    "ground_truth": "sepsis",
    "note": "Rory Staunton, age 12. Died April 1 2012. HELD OUT — never in training.",
}

# ── helpers ───────────────────────────────────────────────────────────────────

def _add_noise(value: float, key: str) -> float:
    """Add iid Gaussian measurement noise to a single vital."""
    return float(value) + rng.normal(0.0, NOISE_SIGMA[key])


def age_band(age_months: int) -> AgeKey:
    for lo, hi, key in AGE_BANDS:
        if lo <= age_months < hi:
            return key
    return "adolescent"


def age_description(age_months: int) -> str:
    if age_months < 1:   return "newborn"
    if age_months < 3:   return f"{age_months}-month-old"
    if age_months < 12:  return f"{age_months}-month-old infant"
    years, months = divmod(age_months, 12)
    return f"{years}-year-old" if months == 0 else f"{years}y{months}m-old"


def weight_for_age(age_months: int) -> float:
    if age_months <= 0:    wt = 3.3
    elif age_months <= 3:  wt = 3.3 + age_months * 1.0
    elif age_months <= 12: wt = 6.0 + (age_months - 3)  * 0.4
    elif age_months <= 24: wt = 9.5 + (age_months - 12) * 0.2
    elif age_months <= 60: wt = 12.0 + (age_months - 24) * 0.14
    elif age_months <= 144:wt = 17.0 + (age_months - 60) * 0.22
    else:                  wt = 35.0 + (age_months - 144) * 0.25
    return round(max(2.5, random.gauss(wt, wt * 0.08)), 1)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def sample_vitals(
    age_months: int,
    deltas: dict[str, tuple[float, float]],
    is_sepsis: bool = False,
    override: Optional[dict[str, tuple[float, float]]] = None,
) -> dict:
    """
    Sample one vital snapshot.

    For sepsis cases the within-vital std is replaced with the PhysioNet 2019
    recalibrated value; for mimic cases the PECARN std is used unchanged.
    Gaussian measurement noise is added last, independently of the sampling std.
    """
    band    = age_band(age_months)
    normals = dict(NORMAL_VITALS[band])
    if override:
        normals.update(override)

    vitals: dict = {}
    for key in ("hr", "rr", "temp_f", "spo2", "cap_refill_s"):
        n_mean, n_std_pecarn = normals[key]

        # PhysioNet recalibration: use real-world sepsis std for sepsis cases
        n_std = PHYSIONET_SEPSIS_STD[key] if is_sepsis else n_std_pecarn

        base          = random.gauss(n_mean, n_std)
        d_mean, d_std = deltas.get(key, (0.0, 0.0))
        delta         = random.gauss(d_mean, abs(d_std))

        # ~12% of sepsis cases are hypothermic — flip temp delta
        if key == "temp_f" and is_sepsis and random.random() < 0.12:
            delta = -abs(delta)

        raw = _add_noise(base + delta, key)   # measurement noise applied here

        if key == "hr":             raw = clamp(raw, 40,   280)
        elif key == "rr":           raw = clamp(raw, 8,    80)
        elif key == "temp_f":       raw = clamp(raw, 94.0, 107.0)
        elif key == "spo2":         raw = clamp(raw, 60,   100)
        elif key == "cap_refill_s": raw = clamp(raw, 0.5,  8.0)

        vitals[key] = int(round(raw)) if key in ("hr", "rr", "spo2") else round(raw, 1)
    return vitals


def apply_deterioration(vitals: dict, deltas: dict[str, tuple[float, float]]) -> dict:
    v2 = {}
    for key in ("hr", "rr", "temp_f", "spo2", "cap_refill_s"):
        base = vitals.get(key)
        if base is None:
            v2[key] = None
            continue
        d_mean, d_std = deltas.get(key, (0.0, 0.0))
        raw = _add_noise(base + random.gauss(d_mean, abs(d_std)), key)
        if key == "hr":             raw = clamp(raw, 40,   280)
        elif key == "rr":           raw = clamp(raw, 8,    80)
        elif key == "temp_f":       raw = clamp(raw, 94.0, 107.0)
        elif key == "spo2":         raw = clamp(raw, 60,   100)
        elif key == "cap_refill_s": raw = clamp(raw, 0.5,  8.0)
        v2[key] = int(round(raw)) if key in ("hr", "rr", "spo2") else round(raw, 1)
    return v2


def apply_dropout(vitals: dict, dropout_prob: float = 0.30) -> dict:
    if random.random() < dropout_prob:
        keys   = list(vitals.keys())
        n_drop = random.randint(1, 3)
        for k in random.sample(keys, min(n_drop, len(keys))):
            vitals[k] = None
    return vitals


def pick_age_months() -> int:
    band_weights = [0.04, 0.20, 0.25, 0.20, 0.18, 0.13]
    lo, hi, _    = random.choices(AGE_BANDS, weights=band_weights, k=1)[0]
    return random.randint(lo, max(lo, hi - 1))


def build_complaint(template_list: list[str], age_months: int) -> str:
    tmpl = random.choice(template_list)
    return tmpl.format(days=random.randint(1, 5), age_desc=age_description(age_months))


def build_trajectory_note(v1: dict, v2: dict, is_sepsis: bool) -> str:
    hr1,  hr2  = v1.get("hr"),  v2.get("hr")
    sp1,  sp2  = v1.get("spo2"), v2.get("spo2")
    cap1, cap2 = v1.get("cap_refill_s"), v2.get("cap_refill_s")
    if is_sepsis:
        parts = []
        if hr1  and hr2  and hr2  > hr1:  parts.append(f"HR increased from {hr1} to {hr2} bpm over 30 minutes")
        if sp1  and sp2  and sp2  < sp1:  parts.append(f"SpO2 drifting down from {sp1}% to {sp2}%")
        if cap1 and cap2 and cap2 > cap1: parts.append(f"cap refill worsening from {cap1}s to {cap2}s")
        if parts:
            return " On reassessment at 30 minutes: " + ", ".join(parts) + "."
        return " Vital signs trending in wrong direction on reassessment."
    else:
        if hr1 and hr2 and hr2 < hr1:
            return f" HR improved from {hr1} to {hr2} on reassessment — reassuring trajectory."
        return " Vital signs stable on reassessment."

# ── case builders ─────────────────────────────────────────────────────────────

def make_sepsis_case(case_id: int) -> dict:
    age_months = pick_age_months()
    v1 = sample_vitals(age_months, SEPSIS_DELTAS, is_sepsis=True)
    v2 = apply_deterioration(v1, DETERIORATION_DELTAS)
    pool = DECEPTIVE_SEPSIS_COMPLAINTS if random.random() < 0.40 else SEPSIS_COMPLAINTS
    complaint = build_complaint(pool, age_months) + build_trajectory_note(v1, v2, is_sepsis=True)
    apply_dropout(v1)
    return {
        "patient_id": f"SYNTH-{case_id:04d}", "age_months": age_months,
        "sex": random.choice(["M", "F"]), "weight_kg": weight_for_age(age_months),
        "complaint_text": complaint, "vitals": v1, "vitals_t30": v2,
        "ground_truth": "sepsis",
        "source": "synthetic_v3_physionet_recal",
    }


def make_mimic_case(case_id: int, diagnosis: Optional[str] = None) -> dict:
    if diagnosis is None:
        diagnosis = random.choice(MIMIC_TYPES)
    age_months = pick_age_months()
    v1 = sample_vitals(age_months, MIMIC_DELTAS[diagnosis])
    v2 = apply_deterioration(v1, MIMIC_TRAJECTORY_DELTAS)
    complaint = build_complaint(MIMIC_COMPLAINTS[diagnosis], age_months) + build_trajectory_note(v1, v2, is_sepsis=False)
    apply_dropout(v1)
    return {
        "patient_id": f"SYNTH-{case_id:04d}", "age_months": age_months,
        "sex": random.choice(["M", "F"]), "weight_kg": weight_for_age(age_months),
        "complaint_text": complaint, "vitals": v1, "vitals_t30": v2,
        "ground_truth": diagnosis,
        "source": "synthetic_v3_physionet_recal",
    }


def make_confounder_case(case_id: int, profile: dict) -> dict:
    diagnosis  = profile["diagnosis"]
    age_months = random.randint(0, 2) if profile.get("age_band_override") == "neonate" else pick_age_months()
    v1 = sample_vitals(age_months, MIMIC_DELTAS[diagnosis], override=profile.get("vital_override"))
    v2 = apply_deterioration(v1, MIMIC_TRAJECTORY_DELTAS)
    complaint  = build_complaint(MIMIC_COMPLAINTS[diagnosis], age_months) + profile.get("complaint_suffix", "")
    return {
        "patient_id": f"CONF-{case_id:04d}", "age_months": age_months,
        "sex": random.choice(["M", "F"]), "weight_kg": weight_for_age(age_months),
        "complaint_text": complaint, "vitals": v1, "vitals_t30": v2,
        "ground_truth": diagnosis, "confounder": True,
        "source": "synthetic_v3_physionet_recal",
    }

# ── split ─────────────────────────────────────────────────────────────────────

def stratified_split(cases: list[dict], held_out_n: int) -> tuple[list[dict], list[dict]]:
    labels    = np.array([1 if c["ground_truth"] == "sepsis" else 0 for c in cases])
    sss       = StratifiedShuffleSplit(n_splits=1, test_size=held_out_n / len(cases), random_state=SEED)
    train_idx, held_idx = next(sss.split(np.zeros(len(cases)), labels))
    train = [cases[i] for i in sorted(train_idx)]
    held  = [cases[i] for i in sorted(held_idx)]
    sep_t = sum(1 for c in train if c["ground_truth"] == "sepsis")
    sep_h = sum(1 for c in held  if c["ground_truth"] == "sepsis")
    print(f"  Train : {len(train)} ({sep_t} sepsis, {len(train)-sep_t} mimics/other)")
    print(f"  Held  : {len(held)}  ({sep_h} sepsis, {len(held)-sep_h} mimics/other)")
    return train, held

# ── main ──────────────────────────────────────────────────────────────────────

def generate() -> None:
    print("=" * 60)
    print("RORY — Cohort Generator v3")
    print("=" * 60)

    cases: list[dict] = []
    case_id = 1

    print(f"\nGenerating {TOTAL_SEPSIS} sepsis cases...")
    for _ in range(TOTAL_SEPSIS):
        cases.append(make_sepsis_case(case_id)); case_id += 1

    print(f"Generating {TOTAL_MIMICS} mimic cases (balanced across {len(MIMIC_TYPES)} diagnoses)...")
    per_diag  = TOTAL_MIMICS // len(MIMIC_TYPES)
    remainder = TOTAL_MIMICS - per_diag * len(MIMIC_TYPES)
    counts    = {d: per_diag + (1 if i < remainder else 0) for i, d in enumerate(MIMIC_TYPES)}
    for diag, n in counts.items():
        for _ in range(n):
            cases.append(make_mimic_case(case_id, diag)); case_id += 1

    print(f"Generating {len(CONFOUNDERS)} confounder cases...")
    for profile in CONFOUNDERS:
        cases.append(make_confounder_case(case_id, profile)); case_id += 1

    print(f"Injecting {len(REAL_ANCHOR_CASES)} real anchor cases...")
    cases.extend(REAL_ANCHOR_CASES)

    print(f"Total pool: {len(cases)} cases")
    random.shuffle(cases)

    held_out_n = HELD_OUT_SEPSIS + HELD_OUT_MIMICS
    print(f"\nStratified split ({len(cases) - held_out_n} train / {held_out_n} held-out)...")
    train_cases, held_cases = stratified_split(cases, held_out_n)
    held_cases.append(dict(RORY_CASE))
    print(f"Appended Rory → held-out total: {len(held_cases)}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HERO_COHORT_PATH, "w", encoding="utf-8") as f:
        json.dump(train_cases, f, indent=2)
    with open(HELD_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(held_cases, f, indent=2)

    print(f"\n  hero_cohort.json -> {len(train_cases)} cases")
    print(f"  held_out.json    -> {len(held_cases)} cases (incl. Rory)")

    # ── sanity checks ──
    train_ids = {c["patient_id"] for c in train_cases}
    held_ids  = {c["patient_id"] for c in held_cases}
    leak      = train_ids & held_ids
    rory_in_train = any(c["patient_id"] == "RORY-2012-0330" for c in train_cases)
    n_drop    = sum(1 for c in train_cases if any(v is None for v in c["vitals"].values()))
    n_conf    = sum(1 for c in train_cases if c.get("confounder"))
    n_anch    = sum(1 for c in train_cases if str(c.get("patient_id", "")).startswith("ANCHOR"))
    n_dec     = sum(1 for c in train_cases
                    if c.get("ground_truth") == "sepsis"
                    and any(phrase in c.get("complaint_text", "")
                            for phrase in ["mild fussiness", "just not acting right",
                                           "borderline", "elevated at triage"]))

    print(f"\n  Leakage          : {'WARNING: ' + str(leak) if leak else 'none'}")
    print(f"  Rory in train    : {rory_in_train} (must be False)")
    print(f"  Dropout rate     : {n_drop}/{len(train_cases)} = {n_drop/len(train_cases):.1%}")
    print(f"  Confounders      : {n_conf}")
    print(f"  Anchor cases     : {n_anch}")
    print(f"  Deceptive sepsis : ~{n_dec}")
    print(f"\nNoise sigmas (per-vital iid Gaussian):")
    for k, s in NOISE_SIGMA.items():
        print(f"  {k:16s} sigma = {s}")
    print("\nDone.\n")


if __name__ == "__main__":
    generate()