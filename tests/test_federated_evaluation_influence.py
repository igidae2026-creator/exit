import os
import tempfile

from federation.federation_adoption import materialize_evaluation
from runtime.evaluation_evolution import evolve_evaluations


def test_federated_evaluation_influence_tracks_external_generations() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            materialize_evaluation("eval_ext", "imported", {"origin_node": "node_d"})
            materialize_evaluation("eval_ext", "adopted", {"origin_node": "node_d"})
            materialize_evaluation("eval_ext", "activated", {"origin_node": "node_d"})
            out = evolve_evaluations(
                {},
                {"novelty_pressure": 0.7, "diversity_pressure": 0.6, "repair_pressure": 0.1},
                {
                    "policy_stagnation": 0.4,
                    "effective_lineage_diversity": 0.5,
                    "domain_activation_rate": 0.5,
                    "imported_evaluation_generations": 1,
                    "adopted_evaluation_generations": 1,
                    "active_external_evaluation_generations": 1,
                },
            )
            assert out["imported_evaluation_generations"] == 1
            assert out["adopted_evaluation_generations"] == 1
            assert out["active_external_evaluation_generations"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
