import os
import tempfile
from pathlib import Path

from metaos_a import DomainEngine


def test_metaos_a_domain_engine_executes_domain_unit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = str(Path(tmp))
        try:
            engine = DomainEngine(goal="explore code", domain_name="code")
            out = engine.step()
            assert out["artifact"]["name"] == "code_domain"
            assert engine.state.tick == 1
            assert engine.state.lineage_counts["code"] == 1
        finally:
            os.environ.pop("METAOS_ROOT", None)
