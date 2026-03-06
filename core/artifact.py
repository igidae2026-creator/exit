from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.event_log import utc_now
from core.registry import lineage_for, register_artifact

ARTIFACT_KINDS = {
    "output",
    "quest",
    "strategy",
    "policy",
    "evaluation",
    "repair",
}


@dataclass(slots=True)
class Artifact:
    kind: str
    payload: dict[str, Any]
    parent_ids: list[str] = field(default_factory=list)
    artifact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = "code_domain"
    quest_id: str | None = None
    source: str = "metaos"
    score: float | None = None
    tick: int = 0
    timestamp: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    storage_path: str | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "artifact_type": self.kind,
            "parent_ids": list(self.parent_ids),
            "domain": self.domain,
            "quest_id": self.quest_id,
            "source": self.source,
            "score": self.score,
            "score_vector": {"score": self.score} if self.score is not None else {},
            "tick": self.tick,
            "timestamp": self.timestamp,
            "created_at": self.timestamp,
            "metadata": dict(self.metadata),
            "storage_path": self.storage_path,
            "payload": dict(self.payload),
        }


def persist_artifact(
    artifact: Artifact,
    *,
    artifact_dir: str | Path = "artifact_store",
    data_dir: str = "data",
) -> Artifact:
    if artifact.kind not in ARTIFACT_KINDS:
        raise ValueError(f"unsupported artifact kind: {artifact.kind}")

    base = Path(artifact_dir)
    target_dir = base / artifact.artifact_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "artifact.json"

    payload = artifact.to_record()
    payload["storage_path"] = str(target_path)
    with target_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)

    artifact.storage_path = str(target_path)
    register_artifact(artifact.to_record(), data_dir=data_dir)
    return artifact


def create_artifact(
    kind: str,
    payload: Mapping[str, Any],
    *,
    parent_ids: Sequence[str] | None = None,
    domain: str = "code_domain",
    quest_id: str | None = None,
    source: str = "metaos",
    score: float | None = None,
    tick: int = 0,
    metadata: Mapping[str, Any] | None = None,
    artifact_dir: str | Path = "artifact_store",
    data_dir: str = "data",
) -> Artifact:
    artifact = Artifact(
        kind=kind,
        payload=dict(payload),
        parent_ids=list(parent_ids or []),
        domain=domain,
        quest_id=quest_id,
        source=source,
        score=score,
        tick=tick,
        metadata=dict(metadata or {}),
    )
    return persist_artifact(artifact, artifact_dir=artifact_dir, data_dir=data_dir)


def write_artifact() -> str:
    artifact = create_artifact("output", {"content": "artifact generated"})
    return artifact.artifact_id


def lineage(artifact_id: str, *, data_dir: str = "data") -> list[dict[str, Any]]:
    return lineage_for(artifact_id, data_dir=data_dir)
