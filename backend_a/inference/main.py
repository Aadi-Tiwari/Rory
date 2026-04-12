"""FastAPI server for RORY Backend A inference.

POST /predict  - runs the full predict pipeline (model + DBSCAN + drift + reasoning)
GET  /healthz  - returns version and status

Run:
    cd backend_a
    python -m uvicorn inference.main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contract.schema import PredictRequest, PredictResponse, Reasoning

from inference.predict import predict

app = FastAPI(title="RORY Backend A", version="rory-v3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(req: PredictRequest):
    try:
        result = predict(
            patient_id=req.patient_id,
            age_months=req.age_months,
            sex=req.sex,
            weight_kg=req.weight_kg,
            complaint_text=req.complaint_text,
            vitals_raw=req.vitals.model_dump(),
        )
        reasoning_objects = [
            Reasoning(
                bullet=r["bullet"] if isinstance(r, dict) else r.bullet,
                weight=r["weight"] if isinstance(r, dict) else r.weight,
                source_field=r["source_field"] if isinstance(r, dict) else r.source_field,
            )
            for r in result["reasoning"]
        ]
        return PredictResponse(
            recommendation=result["recommendation"],
            risk=result["risk"],
            confidence=result["confidence"],
            completeness=result["completeness"],
            outlier_flag=result["outlier_flag"],
            drift_alert=result["drift_alert"],
            cluster_drift=result["cluster_drift"],
            sepsis_confidence_trend=result["sepsis_confidence_trend"],
            reasoning=reasoning_objects,
            model_version=result["model_version"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/healthz")
def health():
    return {"version": "rory-v3", "status": "ok"}
