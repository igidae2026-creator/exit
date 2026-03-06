import os
import tempfile
from pathlib import Path

from metaos_c.domain_discovery import discover_domains


def test_domain_discovery_spawns_and_registers_new_domain() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        try:
            out = discover_domains(
                {"knowledge_density": 0.7, "domain_distribution": {"default": 3}},
                {"novelty_pressure": 0.82, "diversity_pressure": 0.68, "domain_shift_pressure": 0.76},
            )
            assert out
            assert out[0].startswith("civilization_domain_")
            assert (root / "domain_pool.json").exists()
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_REGISTRY", None)
