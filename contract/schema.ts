// RORY v2 shared contract - CANONICAL VERSION.
// Reconciled from Backend A's running contract.
// No "setting" field in PredictRequest (Backend A doesn't use it).

export const CONTRACT_VERSION = "1.0.0";

export type Recommendation = "HOME" | "ED" | "911";
export type Sex = "M" | "F";

export interface VitalSnapshot {
  hr: number | null;
  rr: number | null;
  temp_f: number | null;
  spo2: number | null;
  cap_refill_s: number | null;
}

export interface PredictRequest {
  patient_id: string;
  age_months: number;
  sex: Sex;
  weight_kg: number;
  complaint_text: string;
  vitals: VitalSnapshot;
}

export interface Reasoning {
  bullet: string;
  weight: number;
  source_field: string;
}

export interface PredictResponse {
  recommendation: Recommendation;
  risk: number;
  confidence: number;
  completeness: number;
  outlier_flag: boolean;
  drift_alert: boolean;
  cluster_drift: number;
  sepsis_confidence_trend: number[];
  reasoning: Reasoning[];
  model_version: string;
}
