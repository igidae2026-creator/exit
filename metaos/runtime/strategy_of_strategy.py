from __future__ import annotations

import copy
import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from artifact.registry import register_envelope


DEFAULT_STRATEGY_OF_STRATEGY_REGISTRY = ".metaos_runtime/data/strategy_of_strategy_artifacts.jsonl"
DEFAULT_STRATEGY_OF_STRATEGY = {
    "exploration_emphasis": 0.35,
    "diversification_emphasis": 0.2,
    "reframing_emphasis": 0.12,
    "recombination_emphasis": 0.13,
    "stabilization_emphasis": 0.2,
}


def _registry_path() -> Path:
    path = Path(os.environ.get("METAOS_STRATEGY_OF_STRATEGY_REGISTRY", DEFAULT_STRATEGY_OF_STRATEGY_REGISTRY))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _normalize(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(value)) for value in weights.values()) or 1.0
    return {key: round(max(0.0, float(value)) / total, 4) for key, value in weights.items()}


def evolve_strategy_of_strategy(
    current: Mapping[str, Any] | None = None,
    pressure: Mapping[str, float] | None = None,
    market: Mapping[str, float] | None = None,
    ecology: Mapping[str, float] | None = None,
) -> dict[str, float]:
    pressure = dict(pressure or {})
    market = dict(market or {})
    ecology = dict(ecology or {})
    strategy = copy.deepcopy(dict(current or DEFAULT_STRATEGY_OF_STRATEGY))
    strategy["exploration_emphasis"] = _clamp(
        float(strategy.get("exploration_emphasis", 0.35))
        + 0.08 * float(pressure.get("novelty_pressure", 0.0))
        + 0.06 * (1.0 - float(ecology.get("exploration_health", 0.5)))
    )
    strategy["diversification_emphasis"] = _clamp(
        float(strategy.get("diversification_emphasis", 0.2))
        + 0.08 * float(pressure.get("diversity_pressure", 0.0))
        + 0.05 * (1.0 - float(ecology.get("diversity_health", 0.5)))
    )
    strategy["reframing_emphasis"] = _clamp(
        float(strategy.get("reframing_emphasis", 0.12))
        + 0.08 * float(pressure.get("reframing_pressure", 0.0))
        + 0.05 * (1.0 - float(ecology.get("novelty_health", 0.5)))
    )
    strategy["recombination_emphasis"] = _clamp(
        float(strategy.get("recombination_emphasis", 0.13))
        + 0.07 * float(pressure.get("domain_shift_pressure", 0.0))
        + 0.04 * float(market.get("domain_budget_bias", 0.0))
    )
    strategy["stabilization_emphasis"] = _clamp(
        float(strategy.get("stabilization_emphasis", 0.2))
        + 0.08 * float(pressure.get("repair_pressure", 0.0))
        + 0.05 * (1.0 - float(ecology.get("repair_health", 0.5)))
    )
    return _normalize(strategy)


def register_strategy_of_strategy(
    strategy_of_strategy: Mapping[str, Any],
    pressure: Mapping[str, float],
    market: Mapping[str, float],
    ecology: Mapping[str, float],
    score: float,
    *,
    parent: str | None = None,
) -> str:
    artifact_id = register_envelope(
        aclass="strategy",
        atype="strategy_of_strategy",
        spec={"strategy_of_strategy": dict(strategy_of_strategy)},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}},
        provenance={"pressure": dict(pressure), "market": dict(market), "ecology": dict(ecology), "score": float(score)},
    )
    rec = {
        "id": artifact_id,
        "parent": parent,
        "strategy_of_strategy": dict(strategy_of_strategy),
        "pressure": dict(pressure),
        "market": dict(market),
        "ecology": dict(ecology),
        "score": float(score),
        "t": time.time(),
    }
    with _registry_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return artifact_id


def load_all() -> list[dict[str, Any]]:
    path = _registry_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows
