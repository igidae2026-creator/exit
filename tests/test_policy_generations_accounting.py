import json
import os
import tempfile
from pathlib import Path

from runtime.civilization_memory import civilization_state


def test_policy_generations_account_from_runtime_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        metrics_path = root / "metrics.jsonl"
        metrics_path.write_text(
            "\n".join(
                [
                    json.dumps({"tick": 1, "policy": {"mutation_rate": 0.2, "share_threshold": 0.75}}),
                    json.dumps({"tick": 2, "policy": {"mutation_rate": 0.2, "share_threshold": 0.75}}),
                    json.dumps({"tick": 3, "policy": {"mutation_rate": 0.24, "share_threshold": 0.73}}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            civ = civilization_state()
            assert civ["policy_generations"] == 2
        finally:
            os.environ.pop("METAOS_ROOT", None)

