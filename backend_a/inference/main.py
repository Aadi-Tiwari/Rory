from fastapi import FastAPI
from contract.schema import PredictRequest, PredictResponse, Reasoning

app = FastAPI()

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    return PredictResponse(
        recommendation="ED",
        risk=0.72,
        confidence=0.65,
        completeness=1.0,
        outlier_flag=False,
        drift_alert=False,
        cluster_drift=0.0,
        sepsis_confidence_trend=[0.5, 0.5, 0.5, 0.5, 0.5],
        reasoning=[
            Reasoning(bullet="Stub response", weight=1.0, source_field="none")
        ],
        model_version="1.0.0-stub"
    )

@app.get("/healthz")
def health():
    return {"version": "1.0.0-stub", "status": "ok"}