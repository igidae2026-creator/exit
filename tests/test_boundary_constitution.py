from validation.boundary import validate_boundary
from validation.constitution import validate_constitution


def test_boundary_matches_genesis_roles() -> None:
    out = validate_boundary({
        "human": ["goal", "essence", "constraints", "acceptance"],
        "system": ["exploration", "implementation", "validation", "evolution", "expansion"],
    })
    assert out["ok"] is True


def test_constitution_requires_genesis_pressure_axes() -> None:
    out = validate_constitution({
        "artifact_classes": ["policy", "quest"],
        "pressure_axes": ["novelty", "diversity", "efficiency", "repair", "domain_shift", "reframing"],
    })
    assert out["ok"] is True
