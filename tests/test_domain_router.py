from metaos.runtime.domain_router import route


def test_domain_router_is_single_domain_compatible() -> None:
    routing = route({"domain_shift_pressure": 0.4}, {"domain_budget": 20.0}, domain="default")
    assert routing["selected_domain"] == "default"
    assert "default" in routing["routing_weights"]
