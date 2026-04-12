"""Backend B - httpx client that calls Backend A's /predict and writes results into Foundry."""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from dotenv import load_dotenv

from contract.schema import PredictRequest, PredictResponse

from .ontology_writer import write_regulations_check, write_triage_decision

load_dotenv()

BACKEND_A_URL = os.getenv("BACKEND_A_URL", "http://localhost:8000/predict")


async def run_prediction(
    encounter_id: str,
    patient_mrn: str,
    request: PredictRequest,
) -> PredictResponse:
    """Send a PredictRequest to Backend A, then persist the result to Foundry.

    Returns the raw PredictResponse so the frontend can render immediately while
    Ontology writes happen in the background.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(BACKEND_A_URL, json=request.model_dump())
        resp.raise_for_status()
        response = PredictResponse(**resp.json())

    write_triage_decision(encounter_id=encounter_id, response=response)
    write_regulations_check(
        encounter_id=encounter_id,
        response=response,
        patient_mrn=patient_mrn,
    )

    return response


def new_encounter_id() -> str:
    return f"E_{uuid.uuid4().hex[:8].upper()}"


def new_decision_id() -> str:
    return f"D_{uuid.uuid4().hex[:8].upper()}"


def new_check_id() -> str:
    return f"R_{uuid.uuid4().hex[:8].upper()}"
