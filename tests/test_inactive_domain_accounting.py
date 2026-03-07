import json
import os
import tempfile
from pathlib import Path

from runtime.civilization_memory import civilization_state


def test_inactive_domains_are_separated_from_active_distribution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        os.environ["METAOS_ROOT"] = str(root)
        os.environ["METAOS_CIVILIZATION_MEMORY"] = str(root / "civilization_memory.jsonl")
        (root / "metrics.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"tick": 1, "routing": {"selected_domain": "default"}}),
                    json.dumps({"tick": 2, "routing": {"selected_domain": "alpha"}}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "civilization_memory.jsonl").write_text(
            json.dumps({"kind": "domain_creation", "payload": {"name": "inactive_beta"}}) + "\n",
            encoding="utf-8",
        )
        try:
            civ = civilization_state()
            assert "inactive_beta" in civ["created_domains"]
            assert "inactive_beta" in civ["inactive_domains"]
            assert "inactive_beta" not in civ["active_domains"]
            assert "inactive_beta" not in civ["active_domain_distribution"]
            assert civ["domain_distribution"]["inactive_beta"] == 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
