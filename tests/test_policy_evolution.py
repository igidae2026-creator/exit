import os
import tempfile
from pathlib import Path

from metaos.runtime.policy_runtime import evolve_policy, load_policy_artifact, swap_policy
from strategy.policy_proposals import propose_policy_bundle


def test_policy_evolves_as_immutable_artifact_and_swaps_at_tick_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        os.environ["METAOS_ARTIFACT_STORE"] = str(root / "artifact_store")
        try:
            evolved = evolve_policy({"mutation_rate": 0.3}, pressure={"novelty_pressure": 0.6, "diversity_pressure": 0.4, "efficiency_pressure": 0.2}, tick=7)
            artifact = load_policy_artifact(evolved["artifact_id"])
            bundle_id = propose_policy_bundle({})
            bound = swap_policy(bundle_id, tick=8)
            assert artifact["immutable"] is True
            assert artifact["artifact_type"] == "runtime_policy"
            assert artifact["payload"]["policy"]["mutation_rate"] == 0.3
            assert bound["tick"] == 8
            assert bound["bundle_id"] == bundle_id
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)
