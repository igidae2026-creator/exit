from domains.loader import load_domain


def test_template_domain_loads_without_core_edits() -> None:
    runtime = load_domain("template_domain")
    generated = runtime.generate()
    assert runtime.loop()["core_edits_required"] is False
    assert "artifact_schema" in generated
    assert "resource_contract" in runtime.resources()
