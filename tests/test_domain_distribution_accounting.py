import json
import os
import tempfile
from pathlib import Path

from runtime.civilization_memory import civilization_state


def test_domain_distribution_accounts_for_runtime_observation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        metrics_path = root / "metrics.jsonl"
        metrics_path.write_text(
            "\n".join(
                [
                    json.dumps({"tick": 1, "routing": {"selected_domain": "default"}}),
                    json.dumps({"tick": 2, "routing": {"selected_domain": "alpha"}}),
                    json.dumps({"tick": 3, "routing": {"selected_domain": "alpha"}}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            civ = civilization_state()
            assert civ["domain_distribution"]["alpha"] > 0.0
            assert len(civ["domain_distribution"]) >= 2
        finally:
            os.environ.pop("METAOS_ROOT", None)

