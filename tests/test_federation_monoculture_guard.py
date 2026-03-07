import os
import tempfile

from federation.federation_adoption import materialize_artifact
from runtime.runtime_safety import runtime_safety


def test_federation_monoculture_guard_surfaces_pressure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            for index in range(6):
                materialize_artifact(f"artifact_{index}", "adopted", {"origin_node": "dominant_node"})
            safety = runtime_safety()
            assert 0.0 <= safety["federation_overload_score"] <= 1.0
            assert isinstance(safety["federation_safety_actions"], list)
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
