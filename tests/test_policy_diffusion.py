import os
import tempfile

from runtime.policy_runtime import evolve_policy


def test_policy_diffusion_remains_bounded() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        os.environ["METAOS_NODE_ID"] = "node_policy"
        try:
            out = evolve_policy(
                {"selection_weight_score": 0.4},
                pressure={"efficiency_pressure": 0.2, "novelty_pressure": 0.5, "diversity_pressure": 0.4},
                tick=3,
            )
            assert out["policy_origin"] == "node_policy"
            assert 0.0 <= out["policy_adoption_rate"] <= 1.0
            assert out["policy_diffusion_depth"] >= 0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
            os.environ.pop("METAOS_NODE_ID", None)
