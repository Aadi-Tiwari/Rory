"""
inference/main.py
=================
FastAPI server for RORY — pediatric sepsis triage AI.

Endpoints:
    POST /predict  — run triage inference
    POST /chat     — ElevenLabs conversational agent Q&A
    GET  /healthz  — health check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from contract.schema import PredictRequest, PredictResponse
from inference.predict import predict as run_predict
from inference.chat import chat as run_chat

app = FastAPI(title="RORY", description="Pediatric sepsis triage AI")


# ── /predict ──────────────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        result = run_predict(
            patient_id=req.patient_id,
            age_months=req.age_months,
            sex=req.sex,
            weight_kg=req.weight_kg,
            complaint_text=req.complaint_text,
            vitals_raw=req.vitals.model_dump(),
        )
        return PredictResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── /chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    triage_context: Optional[dict] = None  # pass the full PredictResponse dict


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        result = run_chat(
            message=req.message,
            triage_context=req.triage_context,
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── /healthz ──────────────────────────────────────────────────────────────────

@app.get("/healthz")
def health():
    return {"version": "rory-v3", "status": "ok"}