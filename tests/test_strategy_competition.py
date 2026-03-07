import os
import tempfile

from runtime.strategy_evolution import evolve_strategies


def test_strategy_competition_tracks_origin_adoption_and_survival() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_NODE_ID"] = "strategy_node"
        try:
            out = evolve_strategies(
                {},
                {"novelty_pressure": 0.6, "diversity_pressure": 0.5, "domain_shift_pressure": 0.4, "repair_pressure": 0.1},
                {"success_rate": 0.7, "selected_domain": "default"},
            )
            assert out["strategy_origin"] == "strategy_node"
            assert 0.0 <= out["strategy_adoption"] <= 1.0
            assert 0.0 <= out["strategy_survival_rate"] <= 1.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_NODE_ID", None)
