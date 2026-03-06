from __future__ import annotations

from typing import Any, Mapping


def remember(state: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    memory = dict(state.get("memory", {})) if isinstance(state.get("memory"), Mapping) else {}
    archive = list(memory.get("archive_summaries", []))
    archive.append(dict(entry))
    memory["archive_summaries"] = archive
    return memory


__all__ = ["remember"]
