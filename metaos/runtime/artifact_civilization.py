from __future__ import annotations

from typing import Any, Mapping

from metaos.policy.evaluation_artifact import register_evaluation as _register_evaluation
from metaos.runtime.allocator_artifact import register_allocator_artifact as _register_allocator
from metaos.policy.policy_registry import register_policy as _register_policy
from metaos.registry.artifact_registry import register as _register_artifact
from metaos.runtime.exploration_strategy_artifact import register_strategy as _register_exploration_strategy
from metaos.runtime.strategy_of_strategy import register_strategy_of_strategy as _register_strategy_of_strategy


def register_strategy_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0, novelty: float = 0.0, diversity: float = 0.0, cost: float = 0.0) -> str:
    return _register_artifact(dict(data), parent=parent, atype="strategy", score=score, novelty=novelty, diversity=diversity, cost=cost)


def register_quest_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0, novelty: float = 0.0, diversity: float = 0.0, cost: float = 0.0, quest: Any = None, policy: Any = None) -> str:
    return _register_artifact(dict(data), parent=parent, atype="quest", score=score, novelty=novelty, diversity=diversity, cost=cost, quest=quest, policy=policy)


def register_policy_artifact(policy: Mapping[str, Any], pressure: Mapping[str, float], score: float, *, parent: str | None = None) -> str:
    return _register_policy(policy, pressure, score, parent=parent)


def register_policy_stack_artifact(stack: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0) -> str:
    return _register_artifact(dict(stack), parent=parent, atype="policy_stack", score=score)


def register_evaluation_artifact(evaluation: Mapping[str, Any], pressure: Mapping[str, float], score: float, *, parent: str | None = None) -> str:
    return _register_evaluation(evaluation, pressure, score, parent=parent)


def register_exploration_strategy_artifact(
    strategy: Mapping[str, Any],
    pressure: Mapping[str, float],
    market: Mapping[str, float],
    score: float,
    *,
    parent: str | None = None,
) -> str:
    return _register_exploration_strategy(strategy, pressure, market, score, parent=parent)


def register_strategy_of_strategy_artifact(
    strategy_of_strategy: Mapping[str, Any],
    pressure: Mapping[str, float],
    market: Mapping[str, float],
    ecology: Mapping[str, float],
    score: float,
    *,
    parent: str | None = None,
) -> str:
    return _register_strategy_of_strategy(strategy_of_strategy, pressure, market, ecology, score, parent=parent)


def register_repair_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0, novelty: float = 0.0, diversity: float = 0.0, cost: float = 0.0) -> str:
    return _register_artifact(dict(data), parent=parent, atype="repair", score=score, novelty=novelty, diversity=diversity, cost=cost)


def register_allocator_artifact(allocator: Mapping[str, Any], pressure: Mapping[str, float], workers: int, budgets: Mapping[str, float], *, parent: str | None = None) -> str:
    return _register_allocator(allocator, pressure, workers, budgets, parent=parent)


def register_domain_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0, novelty: float = 0.0, diversity: float = 0.0, cost: float = 0.0) -> str:
    return _register_artifact(dict(data), parent=parent, atype="domain_genome", score=score, novelty=novelty, diversity=diversity, cost=cost)


def register_civilization_selection_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0) -> str:
    return _register_artifact(dict(data), parent=parent, atype="civilization_selection", score=score)


def register_crossbred_domain_artifact(data: Mapping[str, Any], *, parent: str | None = None, score: float = 0.0, novelty: float = 0.0, diversity: float = 0.0, cost: float = 0.0) -> str:
    return _register_artifact(dict(data), parent=parent, atype="crossbred_domain", score=score, novelty=novelty, diversity=diversity, cost=cost)
