from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from genesis.replay import replay_state_hash
from genesis.spine import append_event, append_metrics
from runtime.long_run_validation import validate_long_run


@pytest.mark.skipif(os.environ.get("METAOS_NIGHTLY") != "1", reason="nightly tier only")
def test_nightly_long_run_target() -> None:
    result = validate_long_run(ticks=10000, seed=42, fail_open=True)
    assert result["healthy"] is True


@pytest.mark.skipif(os.environ.get("METAOS_PERF") != "1", reason="perf tier only")
def test_perf_replay_proof_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        try:
            for tick in range(1_000_000):
                append_event("tick_started", {"tick": tick})
                append_metrics({"tick": tick, "score": 0.5, "quest": {"type": "exploration"}, "routing": {"selected_domain": f"d{tick % 12}"}})
            hashes = {replay_state_hash() for _ in range(100)}
            assert len(hashes) == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
