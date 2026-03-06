import os
import tempfile
from pathlib import Path

from metaos.runtime.strategy_of_strategy import evolve_strategy_of_strategy, load_all, register_strategy_of_strategy


def test_strategy_of_strategy_evolves_and_persists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_STRATEGY_OF_STRATEGY_REGISTRY"] = str(Path(tmp) / "strategy_of_strategy.jsonl")
        try:
            strategy = evolve_strategy_of_strategy(
                pressure={"novelty_pressure": 0.9, "domain_shift_pressure": 0.6},
                market={"mutation_bias": 0.4},
                ecology={"exploration_health": 0.3, "repair_health": 0.8},
            )
            artifact_id = register_strategy_of_strategy(strategy, {"novelty_pressure": 0.9}, {"mutation_bias": 0.4}, {"exploration_health": 0.3}, 0.72)
            rows = load_all()
            assert artifact_id
            assert len(rows) == 1
            assert rows[0]["strategy_of_strategy"]["exploration_emphasis"] > 0.0
        finally:
            os.environ.pop("METAOS_STRATEGY_OF_STRATEGY_REGISTRY", None)
