from __future__ import annotations

from typing import Any

from artifact.registry import load_envelope, register_envelope, rows


_CLASS_BY_TYPE = {
    "strategy": "strategy",
    "exploration_strategy": "strategy",
    "strategy_of_strategy": "strategy",
    "allocator": "strategy",
    "quest": "quest",
    "policy": "policy",
    "policy_stack": "policy",
    "evaluation": "evaluation",
    "repair": "repair",
    "domain": "domain",
    "crossbred_domain": "domain",
    "civilization_selection": "strategy",
    "output": "output",
}


def register(
    data: Any,
    parent: str | None = None,
    atype: str = "strategy",
    score: float = 0.0,
    novelty: float = 0.0,
    diversity: float = 0.0,
    cost: float = 0.0,
    quest: Any = None,
    policy: Any = None,
) -> str:
    aclass = _CLASS_BY_TYPE.get(str(atype), "strategy")
    return register_envelope(
        aclass=aclass,
        atype=str(atype),
        spec={"data": data},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={
            "score": float(score),
            "novelty": float(novelty),
            "diversity": float(diversity),
            "cost": float(cost),
            "quest": quest,
            "policy": policy,
        },
    )


def load_all() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows():
        envelope = load_envelope(str(row.get("artifact_id", "")))
        if not envelope:
            continue
        provenance = envelope.get("provenance", {}) if isinstance(envelope.get("provenance"), dict) else {}
        refs = envelope.get("refs", {}) if isinstance(envelope.get("refs"), dict) else {}
        spec = envelope.get("spec", {}) if isinstance(envelope.get("spec"), dict) else {}
        out.append(
            {
                "id": envelope["artifact_id"],
                "type": envelope.get("type"),
                "class": envelope.get("class"),
                "parent": (refs.get("parents") or [None])[0],
                "data": spec.get("data"),
                "score": provenance.get("score", 0.0),
                "novelty": provenance.get("novelty", 0.0),
                "diversity": provenance.get("diversity", 0.0),
                "cost": provenance.get("cost", 0.0),
                "quest": provenance.get("quest"),
                "policy": provenance.get("policy"),
                "t": envelope.get("created_at", 0.0),
            }
        )
    return out
