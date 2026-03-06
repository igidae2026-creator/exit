import os
import tempfile
from pathlib import Path

from artifact.registry import load_envelope
from runtime.strategy_evolution import evolve_strategies


def test_strategy_evolution_registers_lineaged_strategy_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARTIFACT_STORE"] = str(root / "artifact_store")
        try:
            out = evolve_strategies(
                {"exploration_bias": 0.2},
                {"novelty_pressure": 0.8, "diversity_pressure": 0.7, "domain_shift_pressure": 0.6, "repair_pressure": 0.1, "efficiency_pressure": 0.2},
                {"success_rate": 0.9},
            )
            envelope = load_envelope(out["artifact_id"])
            assert out["strategy"]["exploration_bias"] > 0.2
            assert envelope is not None
            assert envelope["artifact_type"] == "exploration_strategy"
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)
