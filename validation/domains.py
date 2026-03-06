from __future__ import annotations

from typing import Any, Mapping


REQUIRED_DOMAIN_CALLS = {"input", "generate", "evaluate", "metrics", "loop"}


def validate_domain_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    calls = set(payload.get("domain_calls", REQUIRED_DOMAIN_CALLS))
    return {"name": "domains", "ok": REQUIRED_DOMAIN_CALLS.issubset(calls)}

