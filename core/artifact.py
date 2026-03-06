from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from core.event_log import append_jsonl, ensure_spine
from core.log import AppendOnlyLogger

ARTIFACT_STORE_DIR = "artifact_store"
BLOB_FILENAME = "artifact.bin"
METADATA_FILENAME = "metadata.json"


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    sha256: str
    size_bytes: int
    created_at: str
    artifact_dir: Path
    blob_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class CreatedArtifact:
    artifact_id: str
    kind: str
    payload: Dict[str, Any]
    parent_ids: list[str]
    domain: str
    quest_id: str
    source: str
    score: float
    tick: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "parent_ids": list(self.parent_ids),
            "domain": self.domain,
            "quest_id": self.quest_id,
            "source": self.source,
            "score": self.score,
            "tick": self.tick,
            "metadata": dict(self.metadata),
        }


class ArtifactStore:
    def __init__(self, store_dir: str | Path = ARTIFACT_STORE_DIR, logger: Optional[AppendOnlyLogger] = None, log_dir: str | Path = ".") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger if logger is not None else AppendOnlyLogger(log_dir=log_dir)

    def create_artifact(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> ArtifactRecord:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        payload = bytes(data)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_dir = self.store_dir / digest
        blob_path = artifact_dir / BLOB_FILENAME
        metadata_path = artifact_dir / METADATA_FILENAME
        try:
            artifact_dir.mkdir(parents=False, exist_ok=False)
            created = True
        except FileExistsError:
            created = False
        if not created:
            return self._load_record(digest)
        created_at = datetime.now(timezone.utc).isoformat()
        user_metadata = dict(metadata or {})
        json.dumps(user_metadata)
        blob_path.write_bytes(payload)
        metadata_obj = {
            "artifact_id": digest,
            "sha256": digest,
            "size_bytes": len(payload),
            "created_at": created_at,
            "metadata": user_metadata,
        }
        metadata_path.write_text(json.dumps(metadata_obj, indent=2, sort_keys=True), encoding="utf-8")
        record = ArtifactRecord(digest, digest, len(payload), created_at, artifact_dir, blob_path, metadata_path)
        registry_payload = {
            "artifact_id": digest,
            "sha256": digest,
            "size_bytes": len(payload),
            "artifact_dir": str(artifact_dir),
            "metadata": user_metadata,
        }
        self.logger.log_event("artifact_created", registry_payload)
        self.logger.log_artifact_registry("artifact_registered", registry_payload)
        return record

    def create_json_artifact(self, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ArtifactRecord:
        return self.create_artifact(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"), metadata=metadata)

    def read_artifact(self, artifact_id: str) -> bytes:
        return self._blob_path(artifact_id).read_bytes()

    def read_json_artifact(self, artifact_id: str) -> Dict[str, Any]:
        row = json.loads(self.read_artifact(artifact_id).decode("utf-8"))
        if not isinstance(row, dict):
            raise ValueError(f"invalid JSON artifact payload: {artifact_id}")
        return row

    def read_metadata(self, artifact_id: str) -> Dict[str, Any]:
        row = json.loads(self._metadata_path(artifact_id).read_text(encoding="utf-8"))
        if not isinstance(row, dict):
            raise ValueError(f"invalid metadata format for artifact {artifact_id}")
        return row

    def exists(self, artifact_id: str) -> bool:
        return self._artifact_dir(artifact_id).is_dir()

    def _load_record(self, artifact_id: str) -> ArtifactRecord:
        metadata = self.read_metadata(artifact_id)
        return ArtifactRecord(
            artifact_id=artifact_id,
            sha256=str(metadata.get("sha256")),
            size_bytes=int(metadata.get("size_bytes", 0)),
            created_at=str(metadata.get("created_at")),
            artifact_dir=self._artifact_dir(artifact_id),
            blob_path=self._blob_path(artifact_id),
            metadata_path=self._metadata_path(artifact_id),
        )

    def _artifact_dir(self, artifact_id: str) -> Path:
        if not artifact_id:
            raise ValueError("artifact_id must be a non-empty string")
        return self.store_dir / artifact_id

    def _blob_path(self, artifact_id: str) -> Path:
        path = self._artifact_dir(artifact_id) / BLOB_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"artifact payload not found: {artifact_id}")
        return path

    def _metadata_path(self, artifact_id: str) -> Path:
        path = self._artifact_dir(artifact_id) / METADATA_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"artifact metadata not found: {artifact_id}")
        return path


def create_artifact(
    kind: str,
    payload: Dict[str, Any],
    *,
    parent_ids: Optional[Iterable[str]] = None,
    domain: str = "code_domain",
    quest_id: str = "",
    source: str = "runtime",
    score: float = 0.0,
    tick: int = 0,
    artifact_dir: str | Path = ARTIFACT_STORE_DIR,
    data_dir: str | Path = "data",
    metadata: Optional[Dict[str, Any]] = None,
) -> CreatedArtifact:
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict")
    if not kind:
        raise ValueError("kind must be non-empty")
    parent_list = [str(item) for item in (parent_ids or []) if item]
    logger = AppendOnlyLogger(log_dir=data_dir)
    store = ArtifactStore(store_dir=artifact_dir, logger=logger, log_dir=data_dir)
    lineage_id = parent_list[0] if parent_list else f"{domain}:{tick or 0}:{kind}"
    combined_metadata = {
        "artifact_type": kind,
        "domain": domain,
        "quest_id": quest_id,
        "source": source,
        "score": float(score),
        "tick": int(tick),
        "parent_ids": parent_list,
        "lineage_id": str((metadata or {}).get("lineage_id") or lineage_id),
        **dict(metadata or {}),
    }
    record = store.create_json_artifact(payload, metadata=combined_metadata)
    registry_row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifact_id": record.artifact_id,
        "kind": kind,
        "parent_ids": parent_list,
        "domain": domain,
        "quest_id": quest_id,
        "source": source,
        "score": float(score),
        "tick": int(tick),
        "payload": dict(payload),
        "metadata": dict(combined_metadata),
    }
    append_jsonl(ensure_spine(data_dir).registry_path, registry_row)
    return CreatedArtifact(
        artifact_id=record.artifact_id,
        kind=kind,
        payload=dict(payload),
        parent_ids=parent_list,
        domain=domain,
        quest_id=quest_id,
        source=source,
        score=float(score),
        tick=int(tick),
        metadata=dict(combined_metadata),
    )


__all__ = ["ARTIFACT_STORE_DIR", "ArtifactRecord", "ArtifactStore", "CreatedArtifact", "create_artifact"]
