from runtime.consumer_api import run_consumer_conformance


def test_runtime_consumer_api_shim_reexports_consumer_conformance():
    assert callable(run_consumer_conformance)
