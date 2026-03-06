import os
import tempfile
from pathlib import Path

from kernel.contracts import POLICY_FAMILIES
from kernel.policy_runtime import bind
from strategy.policy_proposals import propose_policy_bundle


def test_policy_bundle_binds_only_as_bundle_at_tick_boundary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_REGISTRY"] = str(Path(tmp) / "artifact_registry.jsonl")
        os.environ["METAOS_ARTIFACT_STORE"] = str(Path(tmp) / "artifact_store")
        try:
            family_ids = {name: f"{name}-id" for name in POLICY_FAMILIES}
            bundle_id = propose_policy_bundle(family_ids)
            frame = bind(bundle_id, tick=7)
            assert frame.tick == 7
            assert frame.bundle_id == bundle_id
            assert dict(frame.family_ids) == family_ids
        finally:
            os.environ.pop("METAOS_REGISTRY", None)
            os.environ.pop("METAOS_ARTIFACT_STORE", None)

