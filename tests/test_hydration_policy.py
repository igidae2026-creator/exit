from federation.hydration_policy import hydration_policy


def test_hydration_policy_bounds_foreign_origin_concentration() -> None:
    policy = hydration_policy({"foreign_origin_distribution": {"node_a": 9, "node_b": 1}})
    assert policy["origin_concentration_limit"] == 0.78
    assert policy["allowed"] is False
    assert policy["max_hydration_depth"] == 3
