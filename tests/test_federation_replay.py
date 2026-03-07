import json
import os
import tempfile
from pathlib import Path

from federation.federation_exchange import export_artifact, exchange_knowledge
from federation.federation_hydration import hydrate_artifact
from federation.federation_state import federation_state
from genesis.replay import replay_state


def test_federation_replay_is_deterministic_per_node() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        os.environ["METAOS_NODE_ID"] = "node_r"
        try:
            export_artifact("artifact_x", {"value": 1})
            exchange_knowledge({"density": 0.6})
            first = federation_state()
            second = federation_state()
            assert json.dumps(first, sort_keys=True, ensure_ascii=True) == json.dumps(second, sort_keys=True, ensure_ascii=True)
            events = Path(tmp) / "federation" / "events.jsonl"
            assert events.exists()
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
            os.environ.pop("METAOS_NODE_ID", None)


def test_replay_reconstructs_hydrated_artifacts_deterministically() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            hydrate_artifact("artifact_origin", origin_node="node_a", adoption_chain=["node_a", "node_r"])
            first = replay_state()
            second = replay_state()
            assert json.dumps(first["federation_replay"], sort_keys=True, ensure_ascii=True) == json.dumps(second["federation_replay"], sort_keys=True, ensure_ascii=True)
            assert first["federation_replay"]["mirrored_external_artifacts"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
