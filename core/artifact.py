from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

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


class ArtifactStore:
    """Immutable SHA-256 artifact store.

    Layout:
      artifact_store/
        <artifact_id>/
          artifact.bin
          metadata.json
    """

    def __init__(
        self,
        store_dir: str | Path = ARTIFACT_STORE_DIR,
        logger: Optional[AppendOnlyLogger] = None,
        log_dir: str | Path = ".",
    ) -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger if logger is not None else AppendOnlyLogger(log_dir=log_dir)

    def create_artifact(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> ArtifactRecord:
        """Create an artifact from bytes and return its record.

        Artifacts are immutable and content-addressed by SHA-256. If an artifact
        already exists, this method returns the existing record without modifying
        on-disk files.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")

        payload = bytes(data)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_id = digest

        artifact_dir = self.store_dir / artifact_id
        blob_path = artifact_dir / BLOB_FILENAME
        metadata_path = artifact_dir / METADATA_FILENAME

        try:
            artifact_dir.mkdir(parents=False, exist_ok=False)
            created = True
        except FileExistsError:
            created = False

        if not created:
            return self._load_record(artifact_id)

        created_at = datetime.now(timezone.utc).isoformat()
        if metadata is None:
            user_metadata: Dict[str, Any] = {}
        elif isinstance(metadata, dict):
            user_metadata = dict(metadata)
        else:
            raise TypeError("metadata must be a dict if provided")

        # Validate JSON-serializability early to avoid partial writes.
        json.dumps(user_metadata)

        blob_path.write_bytes(payload)

        metadata_obj: Dict[str, Any] = {
            "artifact_id": artifact_id,
            "sha256": digest,
            "size_bytes": len(payload),
            "created_at": created_at,
            "metadata": user_metadata,
        }
        metadata_path.write_text(json.dumps(metadata_obj, indent=2, sort_keys=True), encoding="utf-8")

        record = ArtifactRecord(
            artifact_id=artifact_id,
            sha256=digest,
            size_bytes=len(payload),
            created_at=created_at,
            artifact_dir=artifact_dir,
            blob_path=blob_path,
            metadata_path=metadata_path,
        )

        registry_payload = {
            "artifact_id": artifact_id,
            "sha256": digest,
            "size_bytes": len(payload),
            "artifact_dir": str(artifact_dir),
            "metadata": user_metadata,
        }
        self.logger.log_event("artifact_created", registry_payload)
        self.logger.log_artifact_registry("artifact_registered", registry_payload)

        return record

    def create_json_artifact(self, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ArtifactRecord:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return self.create_artifact(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            metadata=metadata,
        )

    def read_json_artifact(self, artifact_id: str) -> Dict[str, Any]:
        try:
            raw = json.loads(self.read_artifact(artifact_id).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON artifact: {artifact_id}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"invalid JSON artifact payload: {artifact_id}")
        return raw

    def create_artifact_from_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> ArtifactRecord:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return self.create_artifact(text.encode("utf-8"), metadata=metadata)

    def read_artifact(self, artifact_id: str) -> bytes:
        return self._blob_path(artifact_id).read_bytes()

    def read_metadata(self, artifact_id: str) -> Dict[str, Any]:
        metadata_path = self._metadata_path(artifact_id)
        try:
            raw = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid metadata JSON for artifact {artifact_id}") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"invalid metadata format for artifact {artifact_id}")

        return raw

    def exists(self, artifact_id: str) -> bool:
        return self._artifact_dir(artifact_id).is_dir()

    def _load_record(self, artifact_id: str) -> ArtifactRecord:
        metadata = self.read_metadata(artifact_id)
        artifact_dir = self._artifact_dir(artifact_id)
        blob_path = self._blob_path(artifact_id)
        metadata_path = self._metadata_path(artifact_id)

        sha256 = metadata.get("sha256")
        size_bytes = metadata.get("size_bytes")
        created_at = metadata.get("created_at")

        if not isinstance(sha256, str):
            raise ValueError(f"invalid sha256 metadata for artifact {artifact_id}")
        if not isinstance(size_bytes, int):
            raise ValueError(f"invalid size_bytes metadata for artifact {artifact_id}")
        if not isinstance(created_at, str):
            raise ValueError(f"invalid created_at metadata for artifact {artifact_id}")

        return ArtifactRecord(
            artifact_id=artifact_id,
            sha256=sha256,
            size_bytes=size_bytes,
            created_at=created_at,
            artifact_dir=artifact_dir,
            blob_path=blob_path,
            metadata_path=metadata_path,
        )

    def _artifact_dir(self, artifact_id: str) -> Path:
        if not isinstance(artifact_id, str) or not artifact_id:
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
