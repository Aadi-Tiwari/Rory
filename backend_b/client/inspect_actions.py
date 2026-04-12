"""Inspect Foundry action type schemas to learn the exact parameter names.

Usage:
    python -m client.inspect_actions

Prints the JSON schema for each RORY Create action so we can see what
parameter names Foundry expects (they don't always match property names).
"""
from __future__ import annotations

import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_URL = os.getenv("FOUNDRY_WORKSPACE_URL", "").rstrip("/")
TOKEN = os.getenv("FOUNDRY_TOKEN", "")
ONTOLOGY_RID = os.getenv("FOUNDRY_ONTOLOGY_RID", "")

ACTIONS_TO_INSPECT = [
    "create-rory-patient",
    "create-rory-encounter",
    "create-rory-vital-snapshot",
    "create-rory-triage-decision",
    "create-rory-regulations-check",
    "create-rory-protocol-citation",
]


def headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def inspect_action(action_name: str) -> None:
    url = (
        f"{WORKSPACE_URL}/api/v2/ontologies/{ONTOLOGY_RID}"
        f"/actionTypes/{action_name}"
    )
    print(f"\n=== {action_name} ===")
    print(f"URL: {url}")
    try:
        resp = httpx.get(url, headers=headers(), timeout=15.0)
    except httpx.HTTPError as e:
        print(f"Network error: {e}")
        return

    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        # Print parameter names specifically - that's what we need
        params = data.get("parameters", {})
        print(f"Parameter names:")
        if isinstance(params, dict):
            for name, meta in params.items():
                data_type = (meta.get("dataType") or {}).get("type", "?") if isinstance(meta, dict) else "?"
                print(f"  - {name} ({data_type})")
        else:
            print(f"  (unexpected shape: {type(params).__name__})")
        # Also print the full JSON for reference
        print(f"\nFull response:")
        print(json.dumps(data, indent=2)[:3000])
    else:
        print(f"Body: {resp.text[:500]}")


def main() -> None:
    if not WORKSPACE_URL or not TOKEN or not ONTOLOGY_RID:
        print("ERROR: missing env vars in .env")
        sys.exit(1)

    for action in ACTIONS_TO_INSPECT:
        inspect_action(action)


if __name__ == "__main__":
    main()
