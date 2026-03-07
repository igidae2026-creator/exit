import json
import os
import tempfile
from pathlib import Path

from runtime.civilization_state import civilization_state


def test_civilization_state_reports_domain_counts_consistently() -> None:
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
            assert "inactive_domains" in civ
            assert "active_domain_distribution" in civ
            assert "created_domain_count" in civ
            assert "active_domain_count" in civ
            assert civ["created_domain_count"] == len(civ["created_domains"])
            assert civ["active_domain_count"] == len(civ["active_domains"])
            assert sorted(civ["created_domains"]) == sorted(civ["active_domains"] + civ["inactive_domains"])
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_CIVILIZATION_MEMORY", None)
