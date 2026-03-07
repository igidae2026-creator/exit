from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from artifact.registry import rows
from artifact.registry import register_envelope
from federation.federation_state import local_node_id
from runtime.lineage_branching import lineage_branching


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def evolve_strategies(
    current: Mapping[str, Any] | None,
    pressure: Mapping[str, float],
    outcomes: Mapping[str, Any] | None = None,
    *,
    parent: str | None = None,
) -> dict[str, Any]:
    current = dict(current or {})
    pressure = dict(pressure or {})
    outcomes = dict(outcomes or {})
    strategy = {
        "strategy_origin": local_node_id(),
        "exploration_bias": _clamp(float(current.get("exploration_bias", 0.35)) + 0.18 * float(pressure.get("novelty_pressure", 0.0))),
        "selection_bias": _clamp(float(current.get("selection_bias", 0.3)) + 0.14 * float(pressure.get("diversity_pressure", 0.0))),
        "mutation_bias": _clamp(float(current.get("mutation_bias", 0.3)) + 0.12 * float(pressure.get("domain_shift_pressure", 0.0))),
        "repair_bias": _clamp(float(current.get("repair_bias", 0.2)) + 0.20 * float(pressure.get("repair_pressure", 0.0))),
        "archive_bias": _clamp(float(current.get("archive_bias", 0.2)) + 0.10 * float(outcomes.get("success_rate", 0.0))),
    }
    artifact_id = register_envelope(
        aclass="strategy",
        atype="exploration_strategy",
        spec={"strategy": strategy, "outcomes": outcomes},
        refs={"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {"pressure": pressure}},
        provenance={
            "score": float(outcomes.get("success_rate", 0.0)),
            "novelty": float(pressure.get("novelty_pressure", 0.0)),
            "diversity": float(pressure.get("diversity_pressure", 0.0)),
            "efficiency": 1.0 - float(pressure.get("efficiency_pressure", 0.0)),
        },
    )
    prior = [row for row in rows() if str(row.get("artifact_type", row.get("type", ""))) == "exploration_strategy"]
    lineage_counter = Counter(
        str((((row.get("refs") or {}).get("parents") or ["root"])[0]))
        for row in prior
        if isinstance(row.get("refs"), Mapping)
    )
    strategy_generation_count = len(prior) + 1
    strategy_turnover = round(min(1.0, strategy_generation_count / max(1.0, len(lineage_counter) + 3.0)), 4)
    turnover_quality = _clamp((0.55 * float(outcomes.get("success_rate", 0.0))) + (0.25 * float(pressure.get("novelty_pressure", 0.0))) + (0.20 * float(pressure.get("diversity_pressure", 0.0))))
    origin_counter = Counter(
        str((((row.get("payload") or {}).get("strategy") or {}).get("strategy_origin", "local")))
        for row in prior
        if isinstance(row.get("payload"), Mapping)
    )
    origin_counter[local_node_id()] += 1
    strategy_adoption = _clamp(sum(origin_counter.values()) / max(1.0, float(strategy_generation_count or 1)))
    strategy_survival_rate = _clamp(len([count for count in origin_counter.values() if count > 0]) / max(1.0, float(len(origin_counter) or 1)))
    branching = lineage_branching(
        [],
        pressure,
        domain=str(outcomes.get("selected_domain", current.get("selected_domain", "default"))),
        tick=strategy_generation_count,
        policy_stagnation=_clamp(1.0 - turnover_quality),
    )
    return {
        "artifact_id": artifact_id,
        "strategy": strategy,
        "lineage_parent": parent,
        "strategy_generation_count": strategy_generation_count,
        "strategy_turnover": strategy_turnover,
        "policy_turnover_quality": turnover_quality,
        "policy_stagnation": _clamp(1.0 - turnover_quality),
        "strategy_origin": local_node_id(),
        "strategy_adoption": strategy_adoption,
        "strategy_survival_rate": strategy_survival_rate,
        "branch_rate": float(branching.get("branch_rate", 0.0)),
        "merge_rate": float(branching.get("merge_rate", 0.0)),
    }


__all__ = ["evolve_strategies"]
