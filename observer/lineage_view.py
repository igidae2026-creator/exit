from __future__ import annotations

from artifact.lineage import build_lineage_view
from kernel.spine import read_artifact_log


def lineage_projection() -> dict[str, list[str]]:
    return build_lineage_view(read_artifact_log())

