# RORY - Pediatric Sepsis Triage System

Named after Rory Staunton (2012). A tablet a nurse uses in the first 90 seconds of seeing a kid. She types what she's seeing, enters vitals, and gets back HOME / ED / 911 with Rory's Regulations citations.

Built for Los Altos Hacks X, April 11-12 2026.

## Project Structure

```
RORY/
├── contract/                  # Shared Pydantic/TS contract (canonical)
│   ├── schema.py              # PredictRequest, PredictResponse
│   ├── schema.ts              # TypeScript mirror
│   ├── __init__.py
│   └── VERSION
│
├── backend_a/                 # ML / Inference (Person A)
│   ├── contract/              # Backend A's own contract copy (matches shared)
│   └── backend_a/
│       ├── data/              # 974-case synthetic cohort + held-out set
│       ├── models/            # VitalsMLP + TextEncoder + FusionModel
│       │   └── weights/       # dbscan.pkl, train_stats.json
│       │                      # MISSING: best_model.pt (424MB), sepsis_centroid.npy
│       ├── inference/         # FastAPI server, predict pipeline, DBSCAN, drift
│       ├── tests/
│       └── requirements.txt
│
├── backend_b/                 # Palantir Foundry / AIP (Person B)
│   ├── foundry/
│   │   ├── ontology/          # Seed data (52 objects), ontology export
│   │   ├── logic/             # 2 AIP Logic functions (TypeScript source)
│   │   ├── document_intelligence/  # 2 PDFs + extraction config
│   │   └── agent/             # AIP Agent config + scripted exchanges
│   ├── client/                # predict_client.py, ontology_writer.py, bulk_import.py
│   ├── frontend_components/   # 6 React/TSX components
│   ├── .env                   # Foundry credentials (DO NOT COMMIT)
│   └── README.md
│
└── README.md                  # This file
```

## Running Backend A (ML inference server)

### Prerequisites
- Python 3.11
- best_model.pt in backend_a/backend_a/models/weights/ (424MB, must transfer from AMD Dev Cloud)
- sepsis_centroid.npy in same directory (generate via generate_artifacts.py on Dev Cloud)

### Install
```bash
cd backend_a/backend_a
pip install -r requirements.txt
```

### Start the server
```bash
cd backend_a/backend_a
python -m uvicorn inference.main:app --reload --port 8000
```

### Verify
```bash
curl http://localhost:8000/healthz
# {"version": "rory-v3", "status": "ok"}
```

### Run demo cases
```bash
cd backend_a/backend_a
python -m inference.demo_cache
```

Expected output:
- Obvious mimic: HOME, risk=0.00
- Ambiguous+drift: 911, risk=1.00
- Rory Staunton 2012: 911, risk=1.00

## Running Backend B (Palantir Foundry layer)

Backend B is deployed inside Palantir Foundry at https://losaltos.palantirfoundry.com

### What's deployed in Foundry
- 6 RORY object types (RoryPatient, RoryEncounter, RoryVitalSnapshot, RoryTriageDecision, RoryRegulationsCheck, RoryProtocolCitation)
- 4 link types wiring the relationships
- 52 seed objects (10 patients including Rory 2012)
- 2 PDFs in Document Intelligence (Rory's Regulations + Pediatric SSC)
- 2 AIP Logic functions with AI FDE evals (19/20 pass rate)
- 1 AIP Agent (RORY_Triage_Advisor)

### Calling Backend A from Backend B
```bash
cd backend_b
cp .env.example .env  # already done
pip install httpx python-dotenv
python -c "
import asyncio
from contract.schema import PredictRequest, VitalSnapshot
from client.predict_client import run_prediction

req = PredictRequest(
    patient_id='RORY-2012',
    age_months=144,
    sex='M',
    weight_kg=43.0,
    complaint_text='12yo boy scraped arm 2 days ago, fever 104, leg pain, looks pale',
    vitals=VitalSnapshot(hr=138, rr=28, temp_f=104.0, spo2=95, cap_refill_s=3.2)
)

asyncio.run(run_prediction('E_RORY', 'RORY_2012', req))
"
```

## Contract

The shared contract lives in `/contract/schema.py`. Both backends import from it.

Key types:
- `PredictRequest`: patient_id, age_months, sex, weight_kg, complaint_text, vitals
- `PredictResponse`: recommendation, risk, confidence, completeness, outlier_flag, drift_alert, cluster_drift, sepsis_confidence_trend, reasoning, model_version
- `VitalSnapshot`: hr, rr, temp_f, spo2, cap_refill_s (all Optional for adaptive dimensionality)

## Missing Files (Action Required)

| File | Location | How to get it |
|---|---|---|
| `best_model.pt` | `backend_a/backend_a/models/weights/` | Transfer from AMD Dev Cloud JupyterLab (/workspace/rory/backend_a/models/weights/) |
| `sepsis_centroid.npy` | `backend_a/backend_a/models/weights/` | Run `python generate_artifacts.py` on Dev Cloud, then transfer |

Without these, Backend A returns errors on /predict. The demo_cache.py fallback still works for cached cases.

## Demo

Three tablet demo cases:
1. **Case 1 - Viral mimic**: 9yo girl, fever 101, runny nose. Tablet returns GREEN: SEND HOME.
2. **Case 2 - Rory 2012 in ED**: 12yo boy, scraped arm, fever 104, leg pain. Tablet returns RED: SEND TO ED.
3. **Case 3 - Rory 2012 school nurse**: Same case, only temp + HR available. Tablet still returns RED (lowered threshold).

## Prize Targets

- 1st Overall ($1000)
- Best Social Impact (Fifine mics)
- Palantir AIP 1st ($700 + office tour)
- AMD AI 1st ($600 + $500 GPU credits)
