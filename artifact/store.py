from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


DEFAULT_STORE_ROOT = ".metaos_runtime/artifact_store"


def _store_root() -> Path:
    path = Path(os.environ.get("METAOS_ARTIFACT_STORE", DEFAULT_STORE_ROOT))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def put_body(spec: Mapping[str, Any] | None = None, blobs: Mapping[str, Any] | None = None) -> str:
    payload = {"spec": dict(spec or {}), "blobs": dict(blobs or {})}
    digest = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    path = _store_root() / digest
    if not path.exists():
        path.write_bytes(_canonical_bytes(payload))
    return digest


def get_body(body_ref: str) -> dict[str, Any]:
    path = _store_root() / str(body_ref)
    if not path.exists():
        return {"spec": {}, "blobs": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"spec": {}, "blobs": {}}
    if not isinstance(payload, dict):
        return {"spec": {}, "blobs": {}}
    return {"spec": dict(payload.get("spec", {})), "blobs": dict(payload.get("blobs", {}))}

