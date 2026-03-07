import os
import tempfile

from artifact.archive import append_archive, load_archive


def test_federation_artifact_exchange_is_append_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            append_archive("artifact", {"artifact_id": "a1"}, visibility="shared", origin_status="local")
            append_archive("artifact", {"artifact_id": "a2"}, visibility="external", origin_status="external")
            rows = load_archive()
            assert len(rows) == 2
            assert rows[0]["payload"]["artifact_id"] == "a1"
            assert rows[1]["payload"]["artifact_id"] == "a2"
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
