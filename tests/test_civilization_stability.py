import os
import tempfile
from pathlib import Path

from artifact.civilization_registry import civilization_state
from artifact.registry import register_envelope
from metaos.runtime.civilization_stability import civilization_stability
from metaos.runtime.memory_pressure import memory_pressure


def test_civilization_stability_reports_healthy_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARCHIVE"] = str(root / "archive.jsonl")
        try:
            register_envelope(aclass="policy", atype="policy", spec={"policy": {"generation": 1}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"genome": {"name": "default"}, "routing": {"selected_domain": "default"}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"genome": {"name": "science"}, "routing": {"selected_domain": "science"}})
            civ = civilization_state()
            stability = civilization_stability({"diversity_health": 0.7, "exploration_health": 0.72}, civ, memory_pressure())
            assert stability["lineage_survival"] >= 2
            assert stability["domain_growth"] >= 2
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARCHIVE", None)
