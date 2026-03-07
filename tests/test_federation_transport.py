import os
import tempfile

from federation.federation_exchange import export_artifact
from federation.federation_state import federation_state


def test_federation_transport_tracks_queue_depths_and_delivery() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            export_artifact("artifact_q", {"value": 1})
            state = federation_state()
            assert state["send_queue_depth"] > 0
            assert state["receive_queue_depth"] > 0
            assert state["transport_delivery_rate"] > 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
