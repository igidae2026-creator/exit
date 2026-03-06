from validation.system_boundary import validate_system_boundary


def test_boundary_enforcement_accepts_canonical_roles() -> None:
    out = validate_system_boundary(
        {
            "human": ["goal", "essence", "constraints", "acceptance"],
            "system": ["exploration", "implementation", "validation", "evolution", "expansion"],
        }
    )
    assert out["ok"] is True


def test_boundary_enforcement_rejects_human_execution_scope() -> None:
    out = validate_system_boundary(
        {
            "human": ["goal", "essence", "implementation", "acceptance"],
            "system": ["exploration", "validation", "evolution", "expansion"],
        }
    )
    assert out["ok"] is False
