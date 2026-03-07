from __future__ import annotations

from typing import Any, Mapping

from runtime.civilization_memory import remember as append_memory


def remember(state: Mapping[str, Any], entry: Mapping[str, Any]) -> dict[str, Any]:
    memory = dict(state.get("memory", {})) if isinstance(state.get("memory"), Mapping) else {}
    archive = list(memory.get("archive_summaries", []))
    archive.append(dict(entry))
    memory["archive_summaries"] = archive
    append_memory("metaos_c_memory", dict(entry))
    return memory


__all__ = ["remember"]
