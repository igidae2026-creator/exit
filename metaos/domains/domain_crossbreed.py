from __future__ import annotations

import copy
from typing import Any, Mapping

from metaos.domains.domain_recombination import recombine


def _merged_section(section_a: Mapping[str, Any], section_b: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(section_a)
    for key, value in dict(section_b).items():
        if key not in out:
            out[key] = copy.deepcopy(value)
            continue
        current = out[key]
        if isinstance(current, (int, float)) and isinstance(value, (int, float)):
            out[key] = round((float(current) + float(value)) / 2.0, 4)
        elif isinstance(current, Mapping) and isinstance(value, Mapping):
            out[key] = _merged_section(current, value)
    return out


def crossbreed(
    domain_a: Mapping[str, Any],
    domain_b: Mapping[str, Any] | None = None,
    pressure: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    left = dict(domain_a or {})
    if not domain_b:
        clone = recombine(left, None, pressure)
        clone["name"] = str(left.get("name", "default")) + "_variant"
        return clone
    right = dict(domain_b or {})
    merged = recombine(left, right, pressure)
    merged["name"] = str(left.get("name", "default")) + "__" + str(right.get("name", "default"))
    merged["constraints"] = _merged_section(
        dict(left.get("constraints", {})) if isinstance(left.get("constraints"), Mapping) else {},
        dict(right.get("constraints", {})) if isinstance(right.get("constraints"), Mapping) else {},
    )
    merged["evaluation_recipe"] = _merged_section(
        dict(left.get("evaluation_recipe", {})) if isinstance(left.get("evaluation_recipe"), Mapping) else {},
        dict(right.get("evaluation_recipe", {})) if isinstance(right.get("evaluation_recipe"), Mapping) else {},
    )
    merged["mutation_priors"] = _merged_section(
        dict(left.get("mutation_priors", {})) if isinstance(left.get("mutation_priors"), Mapping) else {},
        dict(right.get("mutation_priors", {})) if isinstance(right.get("mutation_priors"), Mapping) else {},
    )
    return merged
