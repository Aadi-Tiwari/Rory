from pydantic import BaseModel
from typing import Optional, Literal, List

class VitalSnapshot(BaseModel):
    hr: Optional[int] = None
    rr: Optional[int] = None
    temp_f: Optional[float] = None
    spo2: Optional[int] = None
    cap_refill_s: Optional[float] = None

class PredictRequest(BaseModel):
    patient_id: str
    age_months: int
    sex: Literal["M", "F"]
    weight_kg: float
    complaint_text: str
    vitals: VitalSnapshot

class Reasoning(BaseModel):
    bullet: str
    weight: float
    source_field: str

from pydantic import BaseModel, ConfigDict

class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    recommendation: Literal["HOME", "ED", "911"]
    risk: float
    confidence: float
    completeness: float
    outlier_flag: bool
    drift_alert: bool
    cluster_drift: float
    sepsis_confidence_trend: List[float]
    reasoning: List[Reasoning]
    model_version: str