import os
import tempfile
from pathlib import Path

from metaos.runtime.domain_pool import get_domain, list_domains, register_domain


def test_domain_pool_registers_and_lists_domains() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_DOMAIN_POOL"] = str(Path(tmp) / "domain_pool.json")
        try:
            register_domain("science", {"name": "science"})
            assert "default" in list_domains()
            assert "science" in list_domains()
            assert get_domain("science")["name"] == "science"
        finally:
            os.environ.pop("METAOS_DOMAIN_POOL", None)
