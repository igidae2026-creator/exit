from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def _root() -> Path:
    return Path(os.environ.get("METAOS_ROOT", ".metaos_runtime"))


def _path() -> Path:
    path = _root() / "ecosystem" / "registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def register_node(node: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(node)
    with _path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return row


def ecosystem_registry_state() -> dict[str, Any]:
    path = _path()
    rows: list[dict[str, Any]] = []
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    registered = [str(row.get("node_id", "")).strip() for row in rows if str(row.get("node_id", "")).strip()]
    active = [str(row.get("node_id", "")).strip() for row in rows if bool(row.get("active", True))]
    return {
        "registered_nodes": sorted(dict.fromkeys(registered)),
        "active_nodes": sorted(dict.fromkeys(active)),
        "rows": rows[-256:],
    }


__all__ = ["ecosystem_registry_state", "register_node"]
