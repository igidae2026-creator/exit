from __future__ import annotations

import copy
from typing import Any, Mapping

from metaos.policy.policy_stack import default_policy_stack, evolve_policy_stack


def normalize_stack(policy: Mapping[str, Any] | None) -> dict[str, dict[str, float]]:
    defaults = default_policy_stack()
    if not policy:
        return defaults
    if all(key in policy for key in defaults):
        out = copy.deepcopy(defaults)
        for section in defaults:
            incoming = policy.get(section, {})
            if isinstance(incoming, Mapping):
                out[section].update({key: round(float(value), 4) for key, value in incoming.items() if key in out[section]})
        return out
    out = copy.deepcopy(defaults)
    out["selection"].update(
        {
            "score": round(float(policy.get("selection_weight_score", out["selection"]["score"])), 4),
            "novelty": round(float(policy.get("selection_weight_novelty", out["selection"]["novelty"])), 4),
            "diversity": round(float(policy.get("selection_weight_diversity", out["selection"]["diversity"])), 4),
            "efficiency": round(float(policy.get("selection_weight_efficiency", out["selection"]["efficiency"])), 4),
        }
    )
    out["mutation"]["rate"] = round(float(policy.get("mutation_rate", out["mutation"]["rate"])), 4)
    out["selection"]["share_threshold"] = round(float(policy.get("share_threshold", 0.75)), 4)
    return out


def flat_policy(stack: Mapping[str, Mapping[str, float]]) -> dict[str, float]:
    selection = dict(stack.get("selection", {}))
    mutation = dict(stack.get("mutation", {}))
    return {
        "selection_weight_score": round(float(selection.get("score", 0.42)), 4),
        "selection_weight_novelty": round(float(selection.get("novelty", 0.23)), 4),
        "selection_weight_diversity": round(float(selection.get("diversity", 0.2)), 4),
        "selection_weight_efficiency": round(float(selection.get("efficiency", 0.15)), 4),
        "mutation_rate": round(float(mutation.get("rate", 0.2)), 4),
        "share_threshold": round(float(selection.get("share_threshold", 0.75)), 4),
    }


def clamp_weight(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(value)) for value in weights.values()) or 1.0
    out = {key: round(max(0.0, float(value)) / total, 4) for key, value in weights.items()}
    correction = round(1.0 - sum(out.values()), 4)
    last_key = next(reversed(out))
    out[last_key] = round(out[last_key] + correction, 4)
    return out


def apply_strategy_mutation(strategy: Mapping[str, float], mutation: Mapping[str, float]) -> dict[str, float]:
    merged = {key: clamp_weight(float(strategy.get(key, 0.0)) + float(mutation.get(key, 0.0))) for key in strategy}
    return normalize_weights(merged)


def apply_evaluation_mutation(evaluation: Mapping[str, float], mutation: Mapping[str, float]) -> dict[str, float]:
    numeric_keys = [key for key, value in evaluation.items() if isinstance(value, (int, float))]
    merged = {
        key: round(clamp_weight(float(evaluation.get(key, 0.0)) + float(mutation.get(key, 0.0)), 0.05, 0.55), 4)
        for key in numeric_keys
    }
    normalized = normalize_weights(merged)
    out = {key: value for key, value in evaluation.items() if key not in numeric_keys}
    out.update(normalized)
    return out


def build_mutation_frame(
    policy: Mapping[str, Any] | None,
    stabilized_pressure: Mapping[str, float],
    stabilized_market: Mapping[str, float],
    cooldown_state: Mapping[str, Any],
) -> dict[str, Any]:
    policy_stack = normalize_stack(policy)
    policy_stack = evolve_policy_stack(policy_stack, stabilized_pressure, stabilized_market, cooldown_state=cooldown_state)
    return {"policy_stack": policy_stack, "flat_policy": flat_policy(policy_stack)}


__all__ = [
    "apply_evaluation_mutation",
    "apply_strategy_mutation",
    "build_mutation_frame",
    "flat_policy",
    "normalize_stack",
]
