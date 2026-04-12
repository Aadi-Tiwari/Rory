"""
inference/chat.py
=================
ElevenLabs conversational agent proxy for RORY.
Text-only Chat Mode — no audio, no microphone, just Q&A.

Setup:
    1. Go to elevenlabs.io → Agents → Create Agent
    2. In agent settings, enable Chat Mode (text-only)
    3. Set system prompt to the RORY_SYSTEM_PROMPT below (or paste it in the dashboard)
    4. Copy the Agent ID
    5. Set env vars:
         ELEVENLABS_API_KEY=your_api_key
         ELEVENLABS_AGENT_ID=your_agent_id

Install:
    pip install elevenlabs
"""

from __future__ import annotations

import os
import asyncio
from typing import Optional

ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY",  "YOUR_API_KEY_HERE")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "YOUR_AGENT_ID_HERE")

RORY_SYSTEM_PROMPT = """
You are RORY, an AI assistant for a pediatric sepsis triage system named after
Rory Staunton — a 12-year-old boy who died on April 1, 2012 from undetected
sepsis after being sent home from the ED twice. His death led to Rory's
Regulations (10 NYCRR 405.4), New York State's mandatory sepsis protocols.

The RORY system helps nurses and clinicians triage pediatric patients by
analyzing vital signs and complaint text, then recommending HOME, ED, or 911.

You can answer questions about:
- What sepsis is and why it is dangerous in children
- Why certain vitals (HR, RR, temp, SpO2, cap refill) are concerning for age
- What the triage recommendations mean (HOME / ED / 911)
- The drift alert and sepsis confidence trend
- Rory's Regulations and the PECARN / Pediatric Surviving Sepsis Campaign guidelines
- General pediatric sepsis recognition and the challenge of early detection
- Why the model flagged a specific case, based on triage context provided

You are not a replacement for clinical judgment. Always remind users that RORY
is a decision-support tool and clinical assessment takes precedence.
Keep responses concise and clinically grounded. Do not make up clinical data.
""".strip()


async def _chat_async(
    message: str,
    triage_context: Optional[dict] = None,
) -> str:
    """
    Send one message to the ElevenLabs agent and return the text response.
    Uses Chat Mode (text-only, no audio interface).
    """
    from elevenlabs.client import AsyncElevenLabs
    from elevenlabs.conversational_ai.conversation import (
        AsyncConversation,
        ConversationInitiationData,
    )

    client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)

    response_parts: list[str] = []

    async def on_response(text: str):
        response_parts.append(text)

    # Build message — inject triage context if provided
    full_message = message
    if triage_context:
        ctx_lines = [
            f"  Recommendation: {triage_context.get('recommendation')}",
            f"  Risk score:     {triage_context.get('risk')}",
            f"  Confidence:     {triage_context.get('confidence')}",
            f"  Completeness:   {triage_context.get('completeness')}",
            f"  Outlier flag:   {triage_context.get('outlier_flag')}",
            f"  Drift alert:    {triage_context.get('drift_alert')}",
            f"  Cluster drift:  {triage_context.get('cluster_drift')}",
            f"  Sepsis trend:   {triage_context.get('sepsis_confidence_trend')}",
            f"  Top reasoning:  {[r['bullet'] for r in triage_context.get('reasoning', [])[:3]]}",
        ]
        full_message = message + "\n\n[Current patient triage context:\n" + "\n".join(ctx_lines) + "\n]"

    config = ConversationInitiationData(
        conversation_config_override={
            "agent": {
                "prompt": {"prompt": RORY_SYSTEM_PROMPT},
            },
            "tts": {"text_only": True},  # Chat Mode — no audio
        }
    )

    conversation = AsyncConversation(
        client=client,
        agent_id=ELEVENLABS_AGENT_ID,
        requires_auth=True,
        audio_interface=None,            # No audio
        config=config,
        callback_agent_response=on_response,
    )

    await conversation.start_session()
    await conversation.send_user_message(full_message)
    await asyncio.sleep(5)              # Wait for response
    await conversation.end_session()
    await conversation.wait_for_session_end()

    return " ".join(response_parts).strip() or "No response from agent."


def chat(
    message: str,
    triage_context: Optional[dict] = None,
) -> dict:
    """
    Sync wrapper for FastAPI. Runs the async chat in a new event loop.

    Args:
        message:        User's question
        triage_context: Optional current PredictResponse dict for patient context

    Returns:
        {"response": str}
    """
    response = asyncio.run(_chat_async(message, triage_context))
    return {"response": response}