from domains.contract import DomainContract
from domains.loader import load_domain


def test_domain_autonomy_contract_is_runtime_local() -> None:
    runtime: DomainContract = load_domain("code")
    artifact = runtime.generate()
    assert callable(runtime.input)
    assert callable(runtime.generate)
    assert callable(runtime.evaluate)
    assert callable(runtime.metrics)
    assert callable(runtime.loop)
    assert callable(runtime.resources)
    assert callable(runtime.genome)
    assert runtime.evaluate(artifact)["valid"] is True
