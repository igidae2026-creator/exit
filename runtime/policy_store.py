from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from artifact.runtime_store import ArtifactStore
from genesis.logger import AppendOnlyLogger


POLICY_NAMES = (
    "selection_policy",
    "mutation_policy",
    "quest_policy",
    "evaluation_policy",
    "repair_policy",
    "quota_policy",
)


DEFAULT_POLICIES: Dict[str, Dict[str, Any]] = {
    "selection_policy": {
        "diversity_bias": 0.55,
        "dominance_threshold": 0.68,
        "anti_collapse_bias": 0.80,
    },
    "mutation_policy": {
        "preferred_ops": ["perturb", "swap", "recombine"],
        "exploration_bias": 0.65,
        "repair_bias": 0.35,
    },
    "quest_policy": {
        "metric_threshold": 0.55,
        "reframing_priority": 0.95,
        "low_diversity_window": 3,
    },
    "evaluation_policy": {
        "minimum_score": 0.48,
        "minimum_novelty": 0.30,
        "minimum_diversity": 0.28,
    },
    "repair_policy": {
        "max_repair_failures": 2,
        "safe_mode_after": 3,
        "retry_limit": 1,
    },
    "quota_policy": {
        "minimum_worker_budget": 1,
        "base_worker_budget": 2,
    },
}


@dataclass(slots=True)
class PolicyArtifact:
    name: str
    artifact_id: str
    definition: Dict[str, Any]


class PolicyRuntime:
    def __init__(self, artifact_store: ArtifactStore, logger: AppendOnlyLogger) -> None:
        self.artifact_store = artifact_store
        self.logger = logger
        self._current: Dict[str, str] = {}
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        for name in POLICY_NAMES:
            if name in self._current:
                continue
            artifact_id = self.register_policy(name, DEFAULT_POLICIES[name], activate=True)
            self._current[name] = artifact_id

    def register_policy(self, name: str, definition: Mapping[str, Any], *, activate: bool = False) -> str:
        self._validate_name(name)
        payload = {
            "policy_name": name,
            "definition": dict(definition),
        }
        record = self.artifact_store.create_json_artifact(
            payload,
            metadata={
                "artifact_type": "policy",
                "policy_name": name,
            },
        )
        self.logger.log_event(
            "policy_registered",
            {
                "policy_name": name,
                "artifact_id": record.artifact_id,
                "definition": dict(definition),
            },
        )
        if activate:
            self.swap_policy(name, record.artifact_id)
        return record.artifact_id

    def swap_policy(self, name: str, artifact_id: str) -> Dict[str, Any]:
        self._validate_name(name)
        payload = self.artifact_store.read_json_artifact(artifact_id)
        policy_name = payload.get("policy_name")
        definition = payload.get("definition")
        if policy_name != name or not isinstance(definition, dict):
            raise ValueError(f"artifact {artifact_id} is not a valid {name}")
        self._current[name] = artifact_id
        self.logger.log_event(
            "policy_swapped",
            {
                "policy_name": name,
                "artifact_id": artifact_id,
                "definition": definition,
            },
        )
        return dict(definition)

    def get_policy(self, name: str) -> Dict[str, Any]:
        self._validate_name(name)
        artifact_id = self._current[name]
        payload = self.artifact_store.read_json_artifact(artifact_id)
        definition = payload.get("definition")
        if not isinstance(definition, dict):
            raise ValueError(f"invalid policy artifact for {name}")
        return dict(definition)

    def current_policy_ids(self) -> Dict[str, str]:
        return dict(self._current)

    def restore_current(self, mapping: Mapping[str, str]) -> None:
        for name, artifact_id in mapping.items():
            if name not in POLICY_NAMES:
                continue
            try:
                self.swap_policy(name, artifact_id)
            except Exception:
                continue

    def snapshot(self) -> Dict[str, PolicyArtifact]:
        snapshot: Dict[str, PolicyArtifact] = {}
        for name, artifact_id in self._current.items():
            snapshot[name] = PolicyArtifact(name=name, artifact_id=artifact_id, definition=self.get_policy(name))
        return snapshot

    def _validate_name(self, name: str) -> None:
        if name not in POLICY_NAMES:
            raise ValueError(f"unknown policy name: {name}")


__all__ = ["DEFAULT_POLICIES", "POLICY_NAMES", "PolicyArtifact", "PolicyRuntime"]
