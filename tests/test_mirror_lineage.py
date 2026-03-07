import os
import tempfile

from artifact.registry import rows
from federation.federation_hydration import hydrate_artifact


def test_mirror_lineage_fields_are_explicit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            hydrate_artifact("artifact_origin", origin_node="node_a", adoption_chain=["node_a", "node_b"], hydration_depth=2)
            mirrored = [row for row in rows() if str(row.get("artifact_scope", "")) == "mirrored"][0]
            assert mirrored["mirror_parent_ids"] == ["artifact_origin"]
            assert mirrored["origin_artifact_id"] == "artifact_origin"
            assert mirrored["origin_node"] == "node_a"
            assert mirrored["hydration_depth"] == 2
            assert mirrored["adoption_chain"] == ["node_a", "node_b"]
        finally:
            os.environ.pop("METAOS_ROOT", None)
