from __future__ import annotations

import copy
import random
from typing import Any, Mapping


BOUNDS = {
    "selection": {"score": (0.1, 0.55), "novelty": (0.1, 0.45), "diversity": (0.08, 0.4), "efficiency": (0.08, 0.35), "share_threshold": (0.55, 0.9)},
    "mutation": {"rate": (0.08, 0.4), "intensity": (0.08, 0.45), "domain_shift_bias": (0.08, 0.4)},
    "quest": {"meta_bias": (0.08, 0.32), "reframing_bias": (0.1, 0.36), "repair_bias": (0.1, 0.4)},
    "evaluation": {"artifact_bias": (0.15, 0.5), "exploration_bias": (0.15, 0.45), "lineage_penalty": (0.08, 0.3)},
    "repair": {"aggressiveness": (0.1, 0.45), "freeze_bias": (0.08, 0.35), "checkpoint_bias": (0.1, 0.4)},
    "allocation": {"mutation": (0.12, 0.4), "replay": (0.12, 0.35), "repair": (0.12, 0.38), "domain": (0.12, 0.35)},
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, float(value))), 4)


def _normalize(values: Mapping[str, float], section: str) -> dict[str, float]:
    adjusted = {key: _clamp(float(value), *BOUNDS.get(section, {}).get(key, (0.05, 1.0))) for key, value in values.items()}
    total = sum(adjusted.values()) or 1.0
    out = {key: round(value / total, 4) for key, value in adjusted.items()}
    correction = round(1.0 - sum(out.values()), 4)
    last_key = next(reversed(out))
    lo, hi = BOUNDS.get(section, {}).get(last_key, (0.05, 1.0))
    out[last_key] = _clamp(out[last_key] + correction, lo, hi)
    return out


def _section(section: str, values: Mapping[str, float]) -> dict[str, float]:
    return {key: _clamp(value, *BOUNDS.get(section, {}).get(key, (0.0, 1.0))) for key, value in values.items()}


def default_policy_stack() -> dict[str, dict[str, float]]:
    return {
        "selection": _normalize(
            {
                "score": 0.42,
                "novelty": 0.23,
                "diversity": 0.2,
                "efficiency": 0.15,
            },
            "selection",
        ),
        "mutation": _section("mutation", {"rate": 0.2, "intensity": 0.18, "domain_shift_bias": 0.22}),
        "quest": _normalize({"meta_bias": 0.22, "reframing_bias": 0.28, "repair_bias": 0.24}, "quest"),
        "evaluation": _normalize({"artifact_bias": 0.35, "exploration_bias": 0.3, "lineage_penalty": 0.2}, "evaluation"),
        "repair": _normalize({"aggressiveness": 0.3, "freeze_bias": 0.22, "checkpoint_bias": 0.26}, "repair"),
        "allocation": _normalize(
            {
                "mutation": 0.27,
                "replay": 0.24,
                "repair": 0.23,
                "domain": 0.26,
            },
            "allocation",
        ),
    }


def evolve_policy_stack(
    stack: Mapping[str, Mapping[str, float]] | None,
    pressure: Mapping[str, float] | None,
    market_state: Mapping[str, float] | None,
    cooldown_state: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, float]]:
    current = copy.deepcopy(dict(stack or default_policy_stack()))
    pressure = dict(pressure or {})
    market_state = dict(market_state or {})
    cooldown_state = dict(cooldown_state or {})

    out = default_policy_stack()
    for section, defaults in out.items():
        source = dict(current.get(section, defaults))
        updated: dict[str, float] = {}
        for key, default_value in defaults.items():
            value = float(source.get(key, default_value))
            delta = random.uniform(-0.03, 0.03)
            if section == "mutation":
                delta += 0.05 * float(pressure.get("novelty_pressure", 0.0))
                delta += 0.04 * float(market_state.get("mutation_bias", 0.0))
            elif section == "quest":
                delta += 0.04 * float(pressure.get("reframing_pressure", 0.0))
                delta += 0.04 * float(pressure.get("repair_pressure", 0.0))
                if key == "meta_bias" and cooldown_state.get("meta_locked"):
                    delta -= 0.08
                if key == "reframing_bias" and cooldown_state.get("reframing_locked"):
                    delta -= 0.08
            elif section == "repair":
                delta += 0.06 * float(pressure.get("repair_pressure", 0.0))
            elif section == "allocation":
                delta += 0.04 * float(market_state.get(f"{key}_bias", market_state.get("domain_budget_bias", 0.0)))
            elif section == "selection":
                delta += 0.03 * float(pressure.get("diversity_pressure", 0.0))
            lo, hi = BOUNDS.get(section, {}).get(key, (0.0, 1.0))
            updated[key] = _clamp(value + delta, lo, hi)
        out[section] = _normalize(updated, section) if section in {"selection", "quest", "evaluation", "repair", "allocation"} else _section(section, updated)
    return out
