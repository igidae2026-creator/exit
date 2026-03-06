from domains.loader import load_domain


def test_code_domain_satisfies_contract() -> None:
    runtime = load_domain("code")
    artifact = runtime.generate()
    assert runtime.input()["language"] == "python"
    assert runtime.evaluate(artifact)["valid"] is True
    assert "score" in runtime.metrics(artifact)
    assert "artifact" in runtime.loop()
    assert "runtime_slots" in runtime.resources()
    assert runtime.genome()["name"] == "code_domain"
