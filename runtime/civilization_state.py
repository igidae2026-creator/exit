from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from federation.federation_state import federation_state
from genesis.replay import replay_state
from runtime.civilization_memory import civilization_state as memory_civilization_state
from runtime.civilization_memory import latest_memory, memory_window, metrics_window
from runtime.ceiling_metrics import CEILING_METRICS, latest_ceiling_metrics
from runtime.domain_lifecycle import domain_lifecycle_state
from runtime.evaluation_lifecycle import evaluation_lifecycle
from runtime.environment_pressure import ENVIRONMENT_SIGNAL_KEYS, latest_environment_signals
from runtime.lineage_branching import lineage_branching
from runtime.long_horizon_stability import long_horizon_stability
from runtime.self_tuning_guardrails import self_tuning_guardrails


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _history_domain_population(history: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in history[-64:]:
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        domain = str(routing.get("selected_domain") or row.get("domain") or "").strip()
        if domain:
            counts[domain] += 1
    return counts


def _history_lineage_population(history: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in history[-64:]:
        artifact_id = str(row.get("artifact_id") or "")
        if artifact_id:
            counts[artifact_id] += 1
            continue
        lineage = row.get("lineage", {}) if isinstance(row.get("lineage"), Mapping) else {}
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        lineage_id = str(lineage.get("selected_lineage") or routing.get("selected_lineage") or routing.get("selected_domain") or row.get("domain") or "default")
        counts[lineage_id] += 1
    return counts


def _history_policy_population(history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unique: set[str] = set()
    active: set[str] = set()
    for row in history:
        policy = row.get("policy", {}) if isinstance(row.get("policy"), Mapping) else {}
        if policy:
            digest = repr(sorted(policy.items()))
            unique.add(digest)
            if row in history[-8:]:
                active.add(digest)
    return {"generations": len(unique), "active": len(active), "archived": max(0, len(unique) - len(active))}


def _history_evaluation_population(history: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    unique: set[str] = set()
    active: set[str] = set()
    active_distribution: Counter[str] = Counter()
    for row in history:
        evaluation = row.get("evaluation", {}) if isinstance(row.get("evaluation"), Mapping) else {}
        if evaluation:
            digest = repr(sorted(evaluation.items()))
            unique.add(digest)
            if row in history[-8:]:
                active.add(digest)
                regime = str(evaluation.get("regime", row.get("evaluation_regime", ""))).strip()
                if regime:
                    active_distribution[regime] += 1
    total = sum(active_distribution.values()) or 1
    return {
        "generations": len(unique),
        "active": len(active),
        "archived": max(0, len(unique) - len(active)),
        "active_distribution": {
            key: round(value / total, 4)
            for key, value in sorted(active_distribution.items())
        },
    }


def _history_artifact_population(history: Sequence[Mapping[str, Any]], base: Mapping[str, Any]) -> dict[str, Any]:
    population = _as_mapping(base.get("artifact_distribution", {}))
    last_population = {}
    for row in reversed(list(history)):
        candidate = row.get("population", {}) if isinstance(row.get("population"), Mapping) else {}
        counts = candidate.get("population_counts", {}) if isinstance(candidate.get("population_counts"), Mapping) else {}
        if counts:
            last_population = {str(key): int(value) for key, value in counts.items()}
            break
    if last_population:
        population.update(last_population)
    return population


def _history_memory_population(history: Sequence[Mapping[str, Any]]) -> int:
    total = 0
    for row in history:
        total += sum(
            1
            for key in ("quest", "policy", "evaluation", "meta_exploration", "repair", "resource_allocation")
            if row.get(key)
        )
    return total


def _turnover_quality(history: Sequence[Mapping[str, Any]], key: str) -> tuple[float, float]:
    if not history:
        return 0.0, 1.0
    digests: list[str] = []
    scores: list[float] = []
    for row in history[-64:]:
        payload = row.get(key, {}) if isinstance(row.get(key), Mapping) else {}
        if payload:
            digests.append(repr(sorted(payload.items())))
            score = float(row.get("score", row.get("novelty", 0.0)) or 0.0)
            scores.append(score)
    unique = len(set(digests))
    churn = unique / max(1.0, float(len(digests) or 1))
    gain = 0.0
    if scores:
        gain = max(0.0, (sum(scores[-8:]) / max(1.0, len(scores[-8:]))) - (sum(scores[:8]) / max(1.0, len(scores[:8]))))
    quality = round(max(0.0, min(1.0, 0.55 * gain + 0.45 * (1.0 - abs(churn - 0.35)))), 4)
    stagnation = round(max(0.0, min(1.0, 1.0 - quality)), 4)
    return quality, stagnation


def _derived_budget_balance(economy_state: Mapping[str, Any], budgets: Mapping[str, Any]) -> tuple[float, float]:
    budget_mix = economy_state.get("budget_mix", {}) if isinstance(economy_state.get("budget_mix"), Mapping) else {}
    if not budget_mix:
        raw = {
            "exploration_budget": float(budgets.get("exploration_budget", economy_state.get("exploration_budget", 0)) or 0.0),
            "mutation_budget": float(budgets.get("mutation_budget", economy_state.get("mutation_budget", 0)) or 0.0),
            "selection_budget": float(budgets.get("selection_budget", economy_state.get("selection_budget_units", economy_state.get("selection_budget", 0))) or 0.0),
            "policy_budget": float(budgets.get("policy_budget", economy_state.get("policy_budget", 0)) or 0.0),
            "evaluation_budget": float(budgets.get("evaluation_budget", economy_state.get("evaluation_budget", 0)) or 0.0),
            "domain_expansion_budget": float(budgets.get("domain_expansion_budget", economy_state.get("domain_expansion_budget", 0)) or 0.0),
            "repair_budget": float(budgets.get("repair_budget", economy_state.get("repair_budget", 0)) or 0.0),
        }
        total = sum(max(0.0, value) for value in raw.values())
        if total > 0.0:
            budget_mix = {key: round(max(0.0, value) / total, 4) for key, value in raw.items()}
    balance = float(economy_state.get("economy_balance_score", 0.0) or 0.0)
    skew = float(economy_state.get("budget_skew", 0.0) or 0.0)
    if budget_mix and balance <= 0.0:
        ideal = 1.0 / float(len(budget_mix))
        skew = round(max(0.0, min(1.0, sum(abs(value - ideal) for value in budget_mix.values()) / 2.0)), 4)
        balance = round(max(0.0, min(1.0, 1.0 - skew)), 4)
    return balance, skew


def _lineage_rows(history: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in history[-128:]:
        lineage = row.get("lineage", {}) if isinstance(row.get("lineage"), Mapping) else {}
        routing = row.get("routing", {}) if isinstance(row.get("routing"), Mapping) else {}
        lineage_id = str(lineage.get("selected_lineage") or routing.get("selected_lineage") or routing.get("selected_domain") or row.get("domain") or "")
        if lineage_id:
            rows.append(
                {
                    "lineage_id": lineage_id,
                    "count": int(lineage.get("branch_budget", 1) or 1),
                    "merge_candidate": bool(lineage.get("merge_candidate", False)),
                }
            )
    return rows


def _dominance_index(lineages: Mapping[str, Any]) -> float:
    counts = [max(0.0, float(value)) for value in lineages.values()]
    total = sum(counts) or 1.0
    return round(max(counts, default=0.0) / total, 4)


def _lineage_survival_rate(lineages: Mapping[str, Any]) -> float:
    counts = [max(0.0, float(value)) for value in lineages.values()]
    if not counts:
        return 0.0
    return round(sum(1.0 for value in counts if value > 0.0) / max(1.0, len(counts)), 4)


def _latest_runtime_frame(
    name: str,
    replay: Mapping[str, Any],
    runtime_state: Mapping[str, Any],
    *,
    allow_memory_lookup: bool,
) -> dict[str, Any]:
    direct = runtime_state.get(name)
    if isinstance(direct, Mapping):
        return dict(direct)
    replay_value = replay.get(name)
    if isinstance(replay_value, Mapping):
        return dict(replay_value)
    if allow_memory_lookup:
        memory_value = latest_memory(name, {})
        return dict(memory_value) if isinstance(memory_value, Mapping) else {}
    return {}


def civilization_state(
    *,
    state: Mapping[str, Any] | None = None,
    history: Sequence[Mapping[str, Any]] | None = None,
    pressure_state: Mapping[str, Any] | None = None,
    exploration_budget: int | None = None,
) -> dict[str, Any]:
    runtime_state = _as_mapping(state)
    explicit_history = history is not None
    history_rows = list(history or [])
    if not history_rows and not runtime_state:
        history_rows = metrics_window(128)
    if history_rows or runtime_state:
        memory_base = memory_civilization_state() if not runtime_state else {}
        base = {
            "artifact_distribution": {},
            "domain_distribution": {},
            "lineage_counts": {},
            "knowledge_density": float(runtime_state.get("knowledge_density", 0.0) or 0.0),
            "memory_growth": float(runtime_state.get("memory_growth", 0.0) or 0.0),
            "policy_generations": int(runtime_state.get("policy_generations", 0) or 0),
            "evaluation_generations": int(runtime_state.get("evaluation_generations", memory_base.get("evaluation_generations", 0)) or 0),
        }
    else:
        base = memory_civilization_state()
    use_replay = not runtime_state and not explicit_history
    replay = replay_state() if use_replay else {}
    replay_civilization = _as_mapping(replay.get("civilization_state", {}))
    allow_memory_lookup = use_replay
    domain_population = Counter(
        {
            str(key): max(1, int(round(float(value) * 1000))) if isinstance(value, float) and value > 0.0 else int(value)
            for key, value in _as_mapping(base.get("domain_distribution", {})).items()
        }
    )
    domain_population.update(_history_domain_population(history_rows))
    lineage_population = Counter(_as_mapping(base.get("lineage_counts", {})))
    lineage_population.update(_history_lineage_population(history_rows))
    artifact_population = _history_artifact_population(history_rows, base)
    policy_population = {"generations": int(base.get("policy_generations", 0)), "active": int(base.get("policy_generations", 0) > 0)}
    policy_population.update(_history_policy_population(history_rows))
    policy_population["generations"] = max(int(policy_population.get("generations", 0)), int(base.get("policy_generations", 0)))
    evaluation_population = {"generations": int(base.get("evaluation_generations", 0)), "active": int(base.get("evaluation_generations", 0) > 0)}
    evaluation_population.update(_history_evaluation_population(history_rows))
    evaluation_population["generations"] = max(int(evaluation_population.get("generations", 0)), int(base.get("evaluation_generations", 0)))
    pressure = _as_mapping(pressure_state or runtime_state.get("pressure_state") or replay.get("pressure_state"))
    budgets = _as_mapping(runtime_state.get("budgets") or replay.get("budgets") or replay.get("last_metrics", {}).get("budgets", {}))
    economy_state = _latest_runtime_frame("exploration_economy_state", replay, runtime_state, allow_memory_lookup=allow_memory_lookup)
    domain_expansion_state = _latest_runtime_frame("domain_expansion_state", replay, runtime_state, allow_memory_lookup=allow_memory_lookup)
    federation = federation_state()
    recent_window = list(history_rows[-32:] if history_rows else (memory_window(32) if allow_memory_lookup else []))
    created_domains = sorted(set(domain_population))
    active_domains = sorted(name for name, count in domain_population.items() if int(count) > 0)
    inactive_domains = sorted(name for name in created_domains if name not in set(active_domains))
    exploration_budget_value = int(
        exploration_budget
        if exploration_budget is not None
        else budgets.get("exploration_budget", runtime_state.get("exploration_budget", 0)) or 0
    )
    budget_cycle = _as_mapping(runtime_state.get("exploration_cycle") or replay.get("archive_state", {}).get("exploration_cycle", {}))
    memory_population = int(base.get("exploration_outcomes", {}).get("memory_rows", 0)) + _history_memory_population(recent_window)
    artifact_distribution = dict(base.get("artifact_distribution", {}))
    domain_distribution = dict(base.get("domain_distribution", {}))
    active_domain_distribution = dict(base.get("active_domain_distribution", {}))
    knowledge_density = float(base.get("knowledge_density", replay_civilization.get("knowledge_density", 0.0)))
    memory_growth = float(base.get("memory_growth", replay_civilization.get("memory_growth", 0.0)))
    lineage_population_dict = dict(lineage_population)
    policy_turnover_quality, policy_stagnation = _turnover_quality(history_rows, "policy")
    evaluation_turnover_quality, evaluation_stagnation = _turnover_quality(history_rows, "evaluation")
    evaluation_lifecycle_state = evaluation_lifecycle(history_rows)
    lineage_branch_state = lineage_branching(
        history_rows,
        pressure,
        domain=str(active_domains[0] if active_domains else "default"),
        tick=len(history_rows) or 1,
        evaluation_generations=int(evaluation_population.get("generations", 0)),
        policy_stagnation=policy_stagnation,
    )
    active_lineage_count = max(int(lineage_branch_state.get("active_lineage_count", 0)), sum(1 for value in lineage_population_dict.values() if int(value) > 0))
    dormant_lineage_count = max(int(lineage_branch_state.get("dormant_lineage_count", 0)), sum(1 for value in lineage_population_dict.values() if int(value) <= 1))
    domain_lifecycle = domain_lifecycle_state(
        {
            "created_domains": created_domains,
            "active_domains": active_domains,
            "inactive_domains": inactive_domains,
        },
        history=history_rows,
        pressure_state=pressure,
    )
    economy_balance_score, budget_skew = _derived_budget_balance(economy_state, budgets)
    lineage_view = {
        "dominance_index": max(0.0, min(0.9999, _dominance_index(lineage_population_dict))),
        "lineage_survival_rate": _lineage_survival_rate(lineage_population_dict),
        "active_lineage_count": active_lineage_count,
        "dormant_lineage_count": dormant_lineage_count,
        "effective_lineage_diversity": round(max(0.0, min(1.0, (0.55 * (1.0 - max(0.0, min(0.9999, _dominance_index(lineage_population_dict))))) + (0.45 * min(1.0, active_lineage_count / 4.0)))), 4),
    }
    long_horizon = long_horizon_stability(
        {
            "knowledge_density": knowledge_density,
            "memory_growth": memory_growth,
            "dominance_index": lineage_view["dominance_index"],
            "lineage_survival_rate": lineage_view["lineage_survival_rate"],
            "created_domain_count": len(created_domains),
            "active_domain_count": len(active_domains),
            "domain_activation_rate": float(domain_lifecycle.get("domain_activation_rate", 0.0)),
            "policy_stagnation": policy_stagnation,
            "evaluation_stagnation": evaluation_stagnation,
            "concentration_streak": int(lineage_branch_state.get("concentration_streak", 0)),
            "active_evaluation_generations": int(evaluation_lifecycle_state.get("active_evaluation_generations", 0)),
            "evaluation_dominance_index": float(evaluation_lifecycle_state.get("evaluation_dominance_index", 0.0)),
        },
        {"economy_balance_score": economy_balance_score, "budget_skew": budget_skew},
        lineage_view,
        history=history_rows,
    )
    guardrails = self_tuning_guardrails(
        {
            "dominance_index": lineage_view["dominance_index"],
            "active_lineage_count": active_lineage_count,
            "active_evaluation_generations": int(evaluation_lifecycle_state.get("active_evaluation_generations", 0)),
            "evaluation_dominance_index": float(evaluation_lifecycle_state.get("evaluation_dominance_index", 0.0)),
        },
        {
            "economy_balance_score": economy_balance_score,
            "diversity_allocation_budget": int(economy_state.get("diversity_allocation_budget", 0)),
            "evaluation_diversity_budget": int(economy_state.get("evaluation_diversity_budget", 0)),
        },
        {
            **long_horizon,
            "concentration_streak": int(lineage_branch_state.get("concentration_streak", 0)),
            "evaluation_concentration_streak": int(long_horizon.get("evaluation_concentration_streak", 0)),
        },
    )
    intervention_actions = list(
        dict.fromkeys(
            list(long_horizon.get("stability_actions", []))
            + list(guardrails.get("guardrail_actions", []))
            + list(economy_state.get("rebalancing_actions", []))
        )
    )
    if not intervention_actions and (
        float(lineage_branch_state.get("branch_rate", 0.0)) > 0.0
        or float(lineage_branch_state.get("evaluation_branch_rate", 0.0)) > 0.0
        or int(economy_state.get("diversity_allocation_budget", 0)) > 0
        or int(economy_state.get("evaluation_diversity_budget", 0)) > 0
    ):
        intervention_actions.append("bounded_diversification_pressure")
    diversification_intervention_count = len(intervention_actions)
    forced_branch_count = int(bool(lineage_branch_state.get("forced_branch"))) + sum(1 for action in guardrails.get("guardrail_actions", []) if action == "force_branching_pressure")
    ceiling_metrics = latest_ceiling_metrics(history_rows if history_rows else metrics_window(64))
    environment_signals = latest_environment_signals(memory_window(64) if allow_memory_lookup else history_rows)
    return {
        "artifact_population": artifact_population,
        "lineage_population": lineage_population_dict,
        "domain_population": dict(domain_population),
        "policy_population": policy_population,
        "evaluation_population": evaluation_population,
        "memory_population": memory_population,
        "knowledge_density": knowledge_density,
        "memory_growth": memory_growth,
        "ceiling_metrics": ceiling_metrics,
        **{key: float(ceiling_metrics.get(key, 0.0)) for key in CEILING_METRICS},
        "environment_signals": environment_signals,
        **{key: float(environment_signals.get(key, 0.0)) for key in ENVIRONMENT_SIGNAL_KEYS},
        "exploration_budget": exploration_budget_value,
        "budget_cycle_count": int(budget_cycle.get("budget_cycle_count", runtime_state.get("budget_cycle_count", 0)) or 0),
        "budget_exhausted": bool(budget_cycle.get("budget_exhausted", runtime_state.get("budget_exhausted", False))),
        "new_cycle_started": bool(budget_cycle.get("new_cycle_started", runtime_state.get("new_cycle_started", False))),
        "pressure_state": pressure,
        "economy_state": economy_state,
        "domain_expansion_state": domain_expansion_state,
        "artifact_distribution": artifact_distribution,
        "domain_distribution": domain_distribution,
        "active_domain_distribution": active_domain_distribution,
        "lineage_counts": dict(base.get("lineage_counts", {})),
        "lineage_survival_rate": _lineage_survival_rate(lineage_population_dict),
        "dominance_index": lineage_view["dominance_index"],
        "effective_lineage_diversity": lineage_view["effective_lineage_diversity"],
        "active_lineage_count": active_lineage_count,
        "dormant_lineage_count": dormant_lineage_count,
        "branch_rate": float(lineage_branch_state.get("branch_rate", 0.0)),
        "merge_rate": float(lineage_branch_state.get("merge_rate", 0.0)),
        "branch_pressure": float(lineage_branch_state.get("branch_pressure", 0.0)),
        "dominance_suppression": float(lineage_branch_state.get("dominance_suppression", 0.0)),
        "dormant_resurrection_candidates": list(lineage_branch_state.get("dormant_resurrection_candidates", [])),
        "lineage_migration_targets": list(lineage_branch_state.get("lineage_migration_targets", [])),
        "concentration_streak": int(lineage_branch_state.get("concentration_streak", 0)),
        "policy_generations": int(policy_population.get("generations", 0)),
        "evaluation_generations": int(evaluation_population.get("generations", 0)),
        "active_policy_generations": int(policy_population.get("active", 0)),
        "archived_policy_generations": int(policy_population.get("archived", 0)),
        "active_evaluation_generations": max(
            int(evaluation_lifecycle_state.get("active_evaluation_generations", 0)),
            int(evaluation_population.get("active", 0)),
            1 if int(evaluation_population.get("generations", 0)) > 0 else 0,
        ),
        "dormant_evaluation_generations": int(evaluation_lifecycle_state.get("dormant_evaluation_generations", 0)),
        "retired_evaluation_generations": int(evaluation_lifecycle_state.get("retired_evaluation_generations", 0)),
        "archived_evaluation_generations": int(evaluation_population.get("archived", 0)),
        "policy_turnover_quality": policy_turnover_quality,
        "evaluation_turnover_quality": evaluation_turnover_quality,
        "policy_stagnation": policy_stagnation,
        "evaluation_stagnation": evaluation_stagnation,
        "evaluation_branch_rate": float(lineage_branch_state.get("evaluation_branch_rate", 0.0)),
        "evaluation_diversity": float(evaluation_lifecycle_state.get("evaluation_diversity", 0.0)),
        "evaluation_dominance_index": float(evaluation_lifecycle_state.get("evaluation_dominance_index", 0.0)),
        "evaluation_retirement_rate": float(evaluation_lifecycle_state.get("evaluation_retirement_rate", 0.0)),
        "evaluation_reactivation_rate": float(evaluation_lifecycle_state.get("evaluation_reactivation_rate", 0.0)),
        "active_evaluation_distribution": dict(evaluation_lifecycle_state.get("active_evaluation_distribution", evaluation_population.get("active_distribution", {}))),
        "created_domains": created_domains,
        "active_domains": list(domain_lifecycle.get("active_domains", active_domains)),
        "inactive_domains": list(domain_lifecycle.get("inactive_domains", inactive_domains)),
        "retired_domains": list(domain_lifecycle.get("retired_domains", [])),
        "resurrectable_domains": list(domain_lifecycle.get("resurrectable_domains", [])),
        "created_domain_count": len(created_domains),
        "active_domain_count": len(domain_lifecycle.get("active_domains", active_domains)),
        "inactive_domain_count": len(domain_lifecycle.get("inactive_domains", inactive_domains)),
        "retired_domain_count": len(domain_lifecycle.get("retired_domains", [])),
        "resurrectable_domain_count": len(domain_lifecycle.get("resurrectable_domains", [])),
        "domain_lifecycle_state": domain_lifecycle,
        "domain_turnover": float(domain_lifecycle.get("domain_turnover", 0.0)),
        "domain_activation_rate": float(domain_lifecycle.get("domain_activation_rate", 0.0)),
        "domain_retirement_rate": float(domain_lifecycle.get("domain_retirement_rate", 0.0)),
        "lineage_domain_matrix": dict(domain_lifecycle.get("lineage_domain_matrix", {})),
        "domain_lineage_coverage": float(domain_lifecycle.get("domain_lineage_coverage", 0.0)),
        "domain_clusters": dict(domain_lifecycle.get("domain_clusters", {})),
        "cluster_activity": dict(domain_lifecycle.get("cluster_activity", {})),
        "domain_competition_index": float(domain_lifecycle.get("domain_competition_index", 0.0)),
        "domain_resource_arbitration_queue": list(domain_lifecycle.get("domain_resource_arbitration_queue", [])),
        "cross_domain_recombination_candidates": list(domain_lifecycle.get("cross_domain_recombination_candidates", [])),
        "domain_migration_candidates": list(domain_lifecycle.get("domain_migration_candidates", [])),
        "domain_niches": dict(domain_lifecycle.get("domain_niches", {})),
        "dormant_domain_reactivation_count": int(domain_lifecycle.get("dormant_domain_reactivation_count", 0)),
        "economy_balance_score": economy_balance_score,
        "budget_skew": budget_skew,
        "rebalancing_actions": list(economy_state.get("rebalancing_actions", [])),
        "diversity_allocation_budget": int(economy_state.get("diversity_allocation_budget", 0)),
        "evaluation_diversity_budget": int(economy_state.get("evaluation_diversity_budget", 0)),
        "federation_nodes": list(federation.get("federation_nodes", [])),
        "shared_artifact_count": int(federation.get("shared_artifact_count", 0)),
        "shared_domain_count": int(federation.get("shared_domain_count", 0)),
        "policy_diffusion_count": int(federation.get("policy_diffusion_count", 0)),
        "knowledge_exchange_count": int((federation.get("knowledge_propagation", {}) if isinstance(federation.get("knowledge_propagation"), dict) else {}).get("knowledge_exchange_events", 0)),
        "federation_topology": dict(federation.get("federation_topology", {})),
        "artifact_exchange_rate": float(federation.get("artifact_exchange_rate", 0.0)),
        "domain_propagation_rate": float(federation.get("domain_propagation_rate", 0.0)),
        "policy_diffusion_rate": float(federation.get("policy_diffusion_rate", 0.0)),
        "knowledge_flow_rate": float(federation.get("knowledge_flow_rate", 0.0)),
        "knowledge_import_count": int(federation.get("knowledge_import_count", 0)),
        "knowledge_export_count": int(federation.get("knowledge_export_count", 0)),
        "observed_external_artifacts": int(federation.get("observed_external_artifacts", 0)),
        "imported_external_artifacts": int(federation.get("imported_external_artifacts", 0)),
        "adopted_external_artifacts": int(federation.get("adopted_external_artifacts", 0)),
        "active_external_artifacts": int(federation.get("active_external_artifacts", 0)),
        "mirrored_external_artifacts": int(federation.get("mirrored_external_artifacts", 0)),
        "active_mirrored_artifacts": int(federation.get("active_mirrored_artifacts", 0)),
        "hydration_rate": float(federation.get("hydration_rate", 0.0)),
        "hydration_depth_distribution": dict(federation.get("hydration_depth_distribution", {})),
        "foreign_origin_distribution": dict(federation.get("foreign_origin_distribution", {})),
        "mirror_lineage_count": int(federation.get("mirror_lineage_count", 0)),
        "imported_domains": int(federation.get("imported_domains", 0)),
        "adopted_domains": int(federation.get("adopted_domains", 0)),
        "active_imported_domains": int(federation.get("active_imported_domains", 0)),
        "observed_external_policies": int(federation.get("observed_external_policies", 0)),
        "adopted_external_policies": int(federation.get("adopted_external_policies", 0)),
        "active_external_policies": int(federation.get("active_external_policies", 0)),
        "imported_evaluation_generations": int(federation.get("imported_evaluation_generations", 0)),
        "adopted_evaluation_generations": int(federation.get("adopted_evaluation_generations", 0)),
        "active_external_evaluation_generations": int(federation.get("active_external_evaluation_generations", 0)),
        "federation_adoption_rate": float(federation.get("federation_adoption_rate", 0.0)),
        "federation_activation_rate": float(federation.get("federation_activation_rate", 0.0)),
        "federation_influence_score": float(federation.get("federation_influence_score", 0.0)),
        "send_queue_depth": int(federation.get("send_queue_depth", 0)),
        "receive_queue_depth": int(federation.get("receive_queue_depth", 0)),
        "adoption_queue_depth": int(federation.get("adoption_queue_depth", 0)),
        "transport_delivery_rate": float(federation.get("transport_delivery_rate", 0.0)),
        "adoption_completion_rate": float(federation.get("adoption_completion_rate", 0.0)),
        "federation_monoculture_score": float(federation.get("federation_monoculture_score", 0.0)),
        "long_horizon_stability": long_horizon,
        "stability_score": float(long_horizon.get("stability_score", 0.0)),
        "drift_score": float(long_horizon.get("drift_score", 0.0)),
        "stagnation_score": float(long_horizon.get("stagnation_score", 0.0)),
        "overexpansion_score": float(long_horizon.get("overexpansion_score", 0.0)),
        "underexploration_score": float(long_horizon.get("underexploration_score", 0.0)),
        "stability_actions": list(long_horizon.get("stability_actions", [])),
        "guardrail_state": dict(guardrails.get("guardrail_state", {})),
        "tuned_thresholds": dict(guardrails.get("tuned_thresholds", {})),
        "guardrail_actions": list(guardrails.get("guardrail_actions", [])),
        "diversification_intervention_count": diversification_intervention_count,
        "forced_branch_count": forced_branch_count,
        "evaluation_concentration_streak": int(long_horizon.get("evaluation_concentration_streak", 0)),
        "exploration_outcomes": dict(base.get("exploration_outcomes", {})),
    }


def update_civilization_state(
    current: Mapping[str, Any] | None = None,
    updates: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if current is not None and updates is None and not kwargs and (
        "history" in current or "event_frame" in current or "civilization_state" in current
    ):
        event_frame = dict(current)
        state = dict(event_frame.get("civilization_state", {})) if isinstance(event_frame.get("civilization_state"), Mapping) else {}
        history_rows = list(event_frame.get("history", [])) if isinstance(event_frame.get("history"), Sequence) else []
        out = civilization_state(state=state, history=history_rows, pressure_state=event_frame.get("pressure_frame"))
        out.update({key: value for key, value in event_frame.items() if key not in {"history", "event_frame"}})
        return out
    out = civilization_state(state=current) if current is None else dict(current)
    if updates is not None:
        event_frame = dict(updates)
        history_rows = event_frame.pop("history", None)
        derived = civilization_state(
            state={**out, **event_frame},
            history=list(history_rows) if isinstance(history_rows, Sequence) else None,
            pressure_state=event_frame.get("pressure_state"),
        )
        out.update(derived)
        out.update(event_frame)
    if kwargs:
        out.update(kwargs)
    return out


def rebuild_civilization_state() -> dict[str, Any]:
    return civilization_state()


def civilization_status() -> dict[str, Any]:
    state = civilization_state()
    return {
        "artifact_population": dict(state.get("artifact_population", {})),
        "domain_population": dict(state.get("domain_population", {})),
        "lineage_population": dict(state.get("lineage_population", {})),
        "knowledge_density": float(state.get("knowledge_density", 0.0)),
        "exploration_budget": int(state.get("exploration_budget", 0)),
        "budget_cycle_count": int(state.get("budget_cycle_count", 0)),
        "stability_score": float(state.get("stability_score", 0.0)),
        "economy_balance_score": float(state.get("economy_balance_score", 0.0)),
        "pressure_summary": dict(state.get("pressure_state", {})),
    }


__all__ = ["civilization_state", "civilization_status", "rebuild_civilization_state", "update_civilization_state"]
