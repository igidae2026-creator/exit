from __future__ import annotations

from typing import Any, Mapping


def validate_domain_artifact(payload: Mapping[str, Any]) -> bool:
    return "name" in payload and "mutation_priors" in payload

