from metaos.policy.policy_stack import default_policy_stack, evolve_policy_stack


def test_default_policy_stack_is_layered_and_serializable() -> None:
    stack = default_policy_stack()
    assert set(stack) == {"selection", "mutation", "quest", "evaluation", "repair", "allocation"}
    assert round(sum(stack["selection"].values()), 4) == 1.0
    assert round(sum(stack["allocation"].values()), 4) == 1.0


def test_evolve_policy_stack_keeps_sections_bounded() -> None:
    stack = evolve_policy_stack(
        default_policy_stack(),
        {"novelty_pressure": 0.9, "repair_pressure": 0.7, "reframing_pressure": 0.8},
        {"mutation_bias": 0.6, "repair_bias": 0.3, "domain_budget_bias": 0.4},
    )
    assert 0.0 <= stack["mutation"]["rate"] <= 1.0
    assert 0.0 <= stack["repair"]["aggressiveness"] <= 1.0
    assert round(sum(stack["selection"].values()), 4) == 1.0
