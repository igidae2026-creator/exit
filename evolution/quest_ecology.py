from __future__ import annotations

from typing import Any

from artifact.lineage import lineage_concentration
from domains.domain_genome import domain_plugin_names


def choose_quest_kind(replay_state: object, pressure_vector: dict[str, float], *, data_dir: str = "data") -> str:
    plateau = int(getattr(replay_state, "plateau_streak", 0) or 0)
    repair = float(pressure_vector.get("repair_pressure", 0.0))
    novelty = float(pressure_vector.get("novelty_pressure", 0.0))
    diversity = float(pressure_vector.get("diversity_pressure", 0.0))
    transfer = float(pressure_vector.get("transfer_pressure", 0.0))
    reframing = float(pressure_vector.get("reframing_pressure", 0.0))
    concentration = lineage_concentration(data_dir)

    if reframing >= 0.7 or concentration >= 0.60:
        return "reframing_quest"
    if transfer >= 0.6:
        return "transfer_quest"
    if repair >= 0.75:
        return "meta_quest"
    if plateau >= 2 or novelty >= 0.55 or diversity >= 0.55:
        return "exploration_quest"
    return "work_quest"


def quest_payload(kind: str, pressure_vector: dict[str, float], *, domain: str = "code_domain") -> dict[str, Any]:
    titles = {
        "work_quest": "Work quest",
        "exploration_quest": "Exploration quest",
        "meta_quest": "Meta quest",
        "reframing_quest": "Reframing quest",
        "transfer_quest": "Transfer quest",
    }
    descriptions = {
        "work_quest": "Exploit the best current strategy in the canonical domain.",
        "exploration_quest": "Search for novelty, diversity, and new surviving lineages.",
        "meta_quest": "Repair policies, quotas, and supervisor behavior under pressure.",
        "reframing_quest": "Reframe the search objective to escape concentration and plateau.",
        "transfer_quest": "Transfer useful artifacts across domains to unlock recombination.",
    }
    return {
        "quest_type": kind,
        "title": titles[kind],
        "description": descriptions[kind],
        "domain": domain,
        "pressure_snapshot": dict(pressure_vector),
    }


def generate_quest_portfolio(replay_state: object, pressure_vector: dict[str, float], *, max_quests: int = 3) -> list[dict[str, Any]]:
    domains = domain_plugin_names()
    primary = choose_quest_kind(replay_state, pressure_vector)
    portfolio = [quest_payload(primary, pressure_vector, domain="code_domain")]
    artifact_count = len(getattr(replay_state, "artifacts", {}) or {})
    noncanonical_domains = [domain for domain in domains if domain != "code_domain"]

    if noncanonical_domains and (artifact_count == 0 or float(pressure_vector.get("domain_shift_pressure", 0.0)) >= 0.5) and len(portfolio) < max_quests:
        portfolio.append(quest_payload("exploration_quest", pressure_vector, domain=noncanonical_domains[0]))
    if float(pressure_vector.get("transfer_pressure", 0.0)) >= 0.4 and noncanonical_domains and len(portfolio) < max_quests:
        portfolio.append(quest_payload("transfer_quest", pressure_vector, domain=noncanonical_domains[min(1, len(noncanonical_domains) - 1)]))
    if float(pressure_vector.get("diversity_pressure", 0.0)) >= 0.4 and noncanonical_domains and len(portfolio) < max_quests:
        portfolio.append(quest_payload("exploration_quest", pressure_vector, domain=noncanonical_domains[min(1, len(noncanonical_domains) - 1)]))
    if float(pressure_vector.get("repair_pressure", 0.0)) >= 0.45 and len(portfolio) < max_quests:
        portfolio.append(quest_payload("meta_quest", pressure_vector, domain="code_domain"))
    return portfolio[:max_quests]
