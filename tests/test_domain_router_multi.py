import os
import tempfile
from pathlib import Path

from metaos.runtime.domain_pool import ensure_seed_domains
from metaos.runtime.domain_router import route


def test_domain_router_multi_domain_produces_secondary_weight() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_DOMAIN_POOL"] = str(Path(tmp) / "domain_pool.json")
        try:
            ensure_seed_domains()
            routing = route(
                {"domain_shift_pressure": 0.7, "diversity_pressure": 0.8},
                {"domain_budget": 40.0},
                domain="default",
                ecology={"diversity_health": 0.2, "exploration_health": 0.3},
                civilization_selection={"selected_artifact_type": "domain"},
                history=[{"routing": {"selected_domain": "default"}}] * 4,
            )
            non_default = {key: value for key, value in routing["routing_weights"].items() if key != "default"}
            assert non_default
            assert any(value > 0.0 for value in non_default.values())
            assert routing["selected_domain"] in routing["routing_weights"]
        finally:
            os.environ.pop("METAOS_DOMAIN_POOL", None)
