# RORY v2 - Backend B (Palantir Foundry / AIP)

Pediatric sepsis triage tablet for school nurses and pediatric ED triage. This directory holds everything Person B owns: the Palantir Foundry layer, AIP Logic functions, Document Intelligence configs, and the frontend components that render regulations and citations.

## What's in this directory

```
backend_b/
├── README.md                          (you are here)
├── pyproject.toml                     Python package config
├── .env.example                       Copy to .env and fill
├── foundry/
│   ├── ontology/
│   │   └── seed_data.json             10 Patients + Encounters + ... ready to bulk-import
│   ├── logic/
│   │   ├── pediatric_thresholds.ts    PALS age-adjusted vital ranges
│   │   └── interpret_cluster_drift.ts Drift number -> plain English
│   ├── document_intelligence/
│   │   ├── extraction_config.json     Config for ingesting both PDFs
│   │   ├── rorys_regs.pdf             (download manually, see below)
│   │   └── pediatric_ssc.pdf          (download manually, see below)
│   └── agent/
│       ├── agent_config.json          AIP Agent system prompt + tools
│       └── scripted_demo.json         2 pre-scripted Q&A exchanges
├── client/
│   ├── predict_client.py              httpx client for Backend A /predict
│   └── ontology_writer.py             Creates TriageDecision + RegulationsCheck
└── frontend_components/
    ├── RegulationsChecklist.tsx
    ├── CitationPdfModal.tsx
    ├── ClusterDriftSparkline.tsx
    ├── RorySplash.tsx
    ├── ForRoryClose.tsx
    └── DemoRunner.tsx
```

## Hour 0 setup (do this first)

1. `cp .env.example .env` and leave Foundry fields blank for now
2. `pip install -e ../contract -e .` to install the shared contract package + Backend B deps
3. Download the two source PDFs and save them at the paths below:
   - `foundry/document_intelligence/rorys_regs.pdf` - New York State Rory's Regulations (10 NYCRR 405.4) from NY DOH public portal
   - `foundry/document_intelligence/pediatric_ssc.pdf` - 2020 Pediatric Surviving Sepsis Campaign from SCCM public portal
4. Download a public photo of Rory Staunton for the splash screen and save it in the frontend project's `public/` folder as `rory_staunton.jpg`

## What Claude scaffolded for you (already done)

- [x] Contract package (`../contract/schema.py` + `schema.ts` + `VERSION`)
- [x] Ontology seed data with 10 patients including Rory 2012 case
- [x] Both AIP Logic functions with PALS ranges + drift interpretation
- [x] Document Intelligence extraction config
- [x] AIP Agent system prompt and 2 scripted exchanges
- [x] predict_client.py + ontology_writer.py with print-stub fallback for pre-Foundry operation
- [x] All 6 frontend components (RegulationsChecklist, CitationPdfModal, ClusterDriftSparkline, RorySplash, ForRoryClose, DemoRunner)

## What you still have to do manually (Foundry UI actions)

These cannot be scripted from Claude - they require logging into the Foundry workspace:

### Hour 1-4: Create the Ontology in Foundry
1. Open Foundry → Ontology Manager → New Ontology named `rory-v2`
2. Create all 6 object types matching the shape in `seed_data.json`:
   - Patient, Encounter, VitalSnapshot, TriageDecision, RegulationsCheck, ProtocolCitation
3. Wire the relationships (Patient -> Encounter, Encounter -> VitalSnapshot, etc.)
4. Bulk-import `foundry/ontology/seed_data.json` via the Ontology Actions UI or Foundry API
5. Copy the Ontology RID into `.env` as `FOUNDRY_ONTOLOGY_RID`
6. Screenshot the Ontology graph view -> save as `foundry/ontology/final_graph.png`

### Hour 4-7: Document Intelligence
1. Upload both PDFs to Foundry Document Intelligence
2. Apply the extraction schema from `extraction_config.json`
3. Run extraction and review output
4. Map extracted sections to ProtocolCitation objects
5. Verify the `pdf_url` anchors work (click each one, should open PDF to the right page)

### Hour 7-9: Deploy Logic functions
1. Create a new AIP Logic module in Foundry named `rory-logic`
2. Paste `pediatric_thresholds.ts` and `interpret_cluster_drift.ts` into the module
3. Deploy both functions, verify they appear in the Logic function panel
4. Test: call `pediatric_vital_thresholds_for_age(144)` - expect hr_range [70, 120]

### Hour 18-20: Record Agent exchanges
1. Create a new AIP Agent named `RORY-Triage-Advisor`
2. Paste the system prompt from `agent_config.json`
3. Grant Ontology access per the config
4. Type each `user_prompt` from `scripted_demo.json` into the Agent chat
5. Verify the responses render with working citation links
6. Save the Agent session so the demo can replay it

## Frontend integration

The `frontend_components/` directory holds React/TSX files meant to be copied into the main frontend repo (probably at `frontend/src/components/`). Dependencies:

```bash
npm install react-pdf framer-motion lucide-react
```

The components read from typed interfaces defined inline (see `RegulationsChecklist.tsx` exports `RegulationsCheck` and `ProtocolCitation`). In the main frontend, import these alongside the TypeScript contract at `../contract/schema.ts`.

## Running the Backend A client for local testing

Before Foundry workspace exists:

```bash
# Assuming Person A has their stub /predict running on localhost:8000
python -c "
import asyncio
from contract.schema import PredictRequest, VitalSnapshot
from client.predict_client import run_prediction

req = PredictRequest(
    patient_id='TEST_001',
    age_months=144,
    sex='M',
    weight_kg=43.0,
    complaint_text='12yo boy scraped arm 2 days ago, fever 104, leg pain, looks pale',
    vitals=VitalSnapshot(hr=138, rr=28, temp_f=104.0, spo2=95, cap_refill_s=3.2),
    setting='ped_ed'
)

asyncio.run(run_prediction('E_TEST', 'TEST_001', req))
"
```

Expected output: stub print of TriageDecision and RegulationsCheck payloads. Once Foundry workspace is live and `.env` is filled, these become real Ontology writes.

## AMD JupyterLab note

The AMD JupyterLab environment you have access to is best used for **Backend A's ML training** (cohort generation, model training, DBSCAN fitting). Backend B runs on your local dev machine because it talks to Foundry directly. If Person A wants to train on the AMD cluster, have them upload `backend_a/` there; `backend_b/` stays local.

## Critical invariants

1. `ProtocolCitation.pdf_url` must always work - it's the highest-trust moment in the demo
2. `TriageDecision.sepsis_confidence_trend` must be populated for every demo case - empty = dead sparkline
3. Ontology seed data must include the Rory 2012 case (mrn `RORY_2012`)
4. `contract/schema.ts` must stay in sync with `schema.py`
5. Both PDFs must be reachable from the frontend - either world-readable URLs or bundled assets

## Cut order if behind

1. Second AIP Agent exchange (drift warning) - save 30 min
2. Extra 5 seed patients - save 30 min
3. interpret_cluster_drift Logic function - save 45 min (sparkline still renders)
4. CitationPdfModal (replace with simple new-tab link) - save 1 hour
5. ClusterDriftSparkline - save 2 hours, only as a last resort

Never cut: Ontology, Document Intelligence, RegulationsChecklist, RorySplash, ForRoryClose.

## Sign-off checklist

- [ ] All 6 object types in Foundry with correct types/links
- [ ] At least 15 seed objects loaded
- [ ] Both PDFs ingested, 20+ ProtocolCitation objects
- [ ] Both Logic functions deployed and callable
- [ ] predict_client.py round-trips to Backend A
- [ ] ontology_writer.py creates real TriageDecision + RegulationsCheck
- [ ] All 5 frontend components render correctly
- [ ] DemoRunner orchestrates 3-case flow from cached responses
- [ ] Both Agent exchanges recorded
- [ ] Full 90-second demo rehearsed 3x
- [ ] Fallback video recorded
- [ ] Q&A defense sheet memorized
