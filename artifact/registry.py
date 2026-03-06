from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

from artifact.store import get_body, put_body
from kernel.contracts import PRIMARY_ARTIFACT_CLASSES, artifact_envelope


DEFAULT_REGISTRY = ".metaos_runtime/data/artifact_registry.jsonl"


def _registry_path() -> Path:
    path = Path(os.environ.get("METAOS_REGISTRY", DEFAULT_REGISTRY))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_envelope(
    *,
    aclass: str,
    atype: str,
    spec: Mapping[str, Any] | None = None,
    blobs: Mapping[str, Any] | None = None,
    refs: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    constraints: Mapping[str, Any] | None = None,
    artifact_id: str | None = None,
    created_at: float | None = None,
    immutable: bool = True,
) -> str:
    if aclass not in PRIMARY_ARTIFACT_CLASSES:
        raise ValueError(f"unsupported artifact class: {aclass}")
    artifact_id = artifact_id or str(uuid.uuid4())
    created_at = time.time() if created_at is None else float(created_at)
    envelope = artifact_envelope(
        artifact_id=artifact_id,
        aclass=aclass,
        atype=atype,
        spec=spec,
        blobs=blobs,
        schema_version="1.0",
        created_at=created_at,
        immutable=immutable,
        refs=refs,
        provenance=provenance,
        constraints=constraints,
    )
    body_ref = put_body(envelope["spec"], envelope["blobs"])
    row = {
        "artifact_id": artifact_id,
        "class": aclass,
        "type": atype,
        "schema_version": envelope["schema_version"],
        "created_at": envelope["created_at"],
        "immutable": envelope["immutable"],
        "refs": envelope["refs"],
        "provenance": envelope["provenance"],
        "constraints": envelope["constraints"],
        "body_ref": body_ref,
    }
    with _registry_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return artifact_id


def rows() -> list[dict[str, Any]]:
    path = _registry_path()
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                out.append(row)
    return out


def load_envelope(artifact_id: str) -> dict[str, Any] | None:
    for row in reversed(rows()):
        if str(row.get("artifact_id")) != str(artifact_id):
            continue
        body = get_body(str(row.get("body_ref", "")))
        return {
            **row,
            "spec": body["spec"],
            "blobs": body["blobs"],
        }
    return None


def iter_by_class(aclass: str) -> Iterable[dict[str, Any]]:
    for row in rows():
        if str(row.get("class")) == str(aclass):
            yield row

