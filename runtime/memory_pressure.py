from __future__ import annotations

from artifact.archive import load_archive, resurrection_replay
from runtime.civilization_memory import civilization_state


def memory_pressure() -> dict[str, float]:
    archive_rows = load_archive()
    extinction_rows = resurrection_replay()
    civ = civilization_state()
    memory_growth = round(max(min(1.0, len(archive_rows) / 240.0), float(civ.get("memory_growth", 0.0))), 4)
    knowledge_density = round(max(min(1.0, len({str(row.get("kind")) for row in archive_rows}) / 16.0), float(civ.get("knowledge_density", 0.0))), 4)
    archive_pressure = round(min(1.0, (len(archive_rows) + (2 * len(extinction_rows))) / 320.0), 4)
    return {
        "memory_growth": memory_growth,
        "knowledge_density": knowledge_density,
        "archive_pressure": archive_pressure,
    }
