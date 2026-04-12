from contract.schema import PredictRequest, PredictResponse, VitalSnapshot, Reasoning

def test_predict_request_roundtrip():
    req = PredictRequest(
        patient_id="test-001",
        age_months=144,
        sex="M",
        weight_kg=40.0,
        complaint_text="fever and lethargy after scraping arm",
        vitals=VitalSnapshot(hr=142, rr=28, temp_f=103.1, spo2=96, cap_refill_s=3.2)
    )
    assert req.patient_id == "test-001"
    assert req.vitals.hr == 142

def test_predict_request_partial_vitals():
    req = PredictRequest(
        patient_id="test-002",
        age_months=24,
        sex="F",
        weight_kg=12.0,
        complaint_text="vomiting and rash",
        vitals=VitalSnapshot(hr=160)  # all others None
    )
    assert req.vitals.rr is None
    assert req.vitals.hr == 160

def test_predict_response_roundtrip():
    resp = PredictResponse(
        recommendation="911",
        risk=0.91,
        confidence=0.84,
        completeness=0.6,
        outlier_flag=False,
        drift_alert=True,
        cluster_drift=-0.42,
        sepsis_confidence_trend=[0.31, 0.45, 0.58, 0.72, 0.85],
        reasoning=[
            Reasoning(bullet="Tachycardia for age", weight=0.6, source_field="hr"),
            Reasoning(bullet="Elevated temperature", weight=0.3, source_field="temp_f"),
            Reasoning(bullet="Complaint consistent with sepsis", weight=0.1, source_field="complaint_text")
        ],
        model_version="1.0.0"
    )
    assert resp.recommendation == "911"
    assert resp.drift_alert is True
    assert len(resp.sepsis_confidence_trend) == 5