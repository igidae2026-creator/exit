from __future__ import annotations

from typing import Any

from artifact.archive import load_archive, resurrection_replay


def memory_pressure() -> dict[str, float]:
    archive_rows = load_archive()
    extinction_rows = resurrection_replay()
    memory_growth = round(min(1.0, len(archive_rows) / 240.0), 4)
    knowledge_density = round(min(1.0, len({str(row.get("kind")) for row in archive_rows}) / 16.0), 4)
    archive_pressure = round(min(1.0, (len(archive_rows) + (2 * len(extinction_rows))) / 320.0), 4)
    return {
        "memory_growth": memory_growth,
        "knowledge_density": knowledge_density,
        "archive_pressure": archive_pressure,
    }
