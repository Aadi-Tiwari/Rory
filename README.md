# Rory

A research prototype for exploring pediatric triage interfaces, structured vital-sign inputs, model inference, and protocol citations.

The repository contains a Next.js tablet interface, a Python inference service, a shared request/response contract, and Palantir Foundry integration code. The training cohort is synthetic. The project is not clinically validated and must not guide patient care.

## Current availability

The repository does not include `backend_a/models/weights/best_model.pt`. The interface and non-inference tests can run without it. A prediction requires the matching trained checkpoint and the other model assets. Missing inference files return a service-unavailable response rather than a fabricated prediction.

`inference.demo_cache` calls the real prediction pipeline. It is not an offline fallback for a missing checkpoint.

A checkpoint was recovered in an older local checkout, but its original training provenance is incomplete and it is not distributed here. The [research workflow](docs/RESEARCH.md) records its identity and explains how to evaluate a trusted local checkpoint without presenting synthetic results as clinical evidence.

## Research preparation

The repository now includes a cohort leakage audit, frozen CPU inference with artifact hashes, and an evaluator that uses the same decision policy as the service. It reports missed cases, false alarms, calibration, uncertainty, and exploratory subgroup results. The current synthetic data contains later reassessment information and repeated complaint templates; it cannot support an arrival-time clinical validation claim. See the [protocol, data routes, and runnable commands](docs/RESEARCH.md).

There is no clinical partner or suitable approved incident-sepsis cohort yet. The [retrospective study specification](docs/retrospective-study.md) defines that provisional research question, and the [evaluation guide](docs/retrospective-evaluation.md) documents its data requirements and frozen scorer. MIT licensing does not confer clinical validation or permission to use third-party data.

A separate [public admission benchmark](reports/public-triage-2026-10-20/results.md) tested the frozen checkpoint on real pediatric records with narrative text and numeric capillary refill omitted. Performance in that restricted setting was poor. This is an admission-association study, not validation of sepsis detection or HOME / ED / 911 safety. The [benchmark protocol](docs/public-triage-benchmark.md) records the source, exclusions, missing inputs, and thresholds. The [dataset-access review](research_notes/patient-evaluation-access-2026-10-20/open-cohorts.md) and [unsent clinical collaboration request](docs/clinical-collaboration-draft.md) cover the remaining clinical study requirements.

## Frontend

Use Node.js 22:

```sh
cd frontend
npm ci
npm run dev
```

Open <http://localhost:3000/demo> and enable demo mode to explore saved illustrative presets without the backend or checkpoint. Results identify these as saved examples; no inference runs in this mode. The interface is a demonstration; its labels and thresholds are not medical advice.

To point live mode at a different backend, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` before starting or building the interface. Its default is `http://localhost:8000`.

## Inference service

Use a Python 3.11 virtual environment. From `backend_a/`:

```sh
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python -m uvicorn inference.main:app --host 127.0.0.1 --port 8000
```

Place a trusted checkpoint from this project's training pipeline at `models/weights/best_model.pt` before requesting inference. Model loading uses tensor weights rather than unrestricted checkpoint deserialization. Other existing serialized artifacts also need a trusted source.

Inference runs all model components on CPU. The pinned scikit-learn version matches the saved DBSCAN artifact; changing that dependency requires regenerating and checking the artifact.

`GET /healthz` reports process health and whether the checkpoint file exists. File presence is not proof that the checkpoint loads correctly. `POST /predict` uses the types in `contract/schema.py`.

## Project layout

- `frontend/`: tablet and presentation interface.
- `contract/`: shared Python and TypeScript request/response definitions.
- `backend_a/`: synthetic data, models, inference, and backend tests.
- `backend_b/`: Foundry clients, ontology configuration, citation integration, and reusable interface components.
- `tests/`: shared-contract checks.

The Foundry layer requires separate workspace credentials and configuration. Local source files do not prove that a live workspace is deployed or available. See [backend_b/README.md](backend_b/README.md) for integration notes; do not run import or write operations against a workspace merely to preview the interface.

## Checks

From the repository root:

```sh
python -m pytest -q tests backend_a/tests
```

From `frontend/`:

```sh
npm run build
```

Tests cover contract behavior, inference helpers, and failure when the checkpoint is absent. They do not establish clinical safety, external Foundry availability, or a functioning end-to-end prediction without the missing model.

Preset results preserve the entered vital signs and identify their saved explanations. The results page provides prototype review steps rather than a clinical care plan.

## License

Original project source is available under the [MIT License](LICENSE). Third-party dependencies, model weights, fonts, documents, and datasets retain their own licenses. This license does not grant rights to third-party assets.
