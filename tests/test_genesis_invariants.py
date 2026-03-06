import os
import tempfile
from pathlib import Path

from artifact.registry import register_envelope
from kernel.invariants import enforce
from kernel.spine import append_event, append_metrics


def test_genesis_invariants_hold_for_append_only_truth() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_EVENT_LOG"] = str(root / "events.jsonl")
        os.environ["METAOS_METRICS"] = str(root / "metrics.jsonl")
        os.environ["METAOS_REGISTRY"] = str(root / "artifact_registry.jsonl")
        try:
            append_event("tick_started", {"tick": 1})
            append_metrics({"tick": 1, "score": 0.7, "routing": {"selected_domain": "default"}, "policy": {"mutation_rate": 0.2}, "quest": {"type": "exploration"}})
            register_envelope(aclass="policy", atype="policy", spec={"policy": {"mutation_rate": 0.2}})
            register_envelope(aclass="domain", atype="domain_genome", spec={"genome": {"name": "default"}, "routing": {"selected_domain": "default"}})
            out = enforce(minimum_lineages=1)
            assert out["append_only_logs"]["ok"] is True
            assert out["immutable_artifacts"]["ok"] is True
            assert out["replay_determinism"]["ok"] is True
        finally:
            for key in ("METAOS_ROOT", "METAOS_EVENT_LOG", "METAOS_METRICS", "METAOS_REGISTRY"):
                os.environ.pop(key, None)
