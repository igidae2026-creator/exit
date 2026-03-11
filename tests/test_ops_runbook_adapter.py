from metaos.adapters.ops_runbook import adapter_manifest


def test_ops_runbook_adapter_manifest_shape():
    manifest = adapter_manifest()

    assert manifest["adapter_name"] == "ops_runbook"
    assert manifest["contract_version"] == "1.0.0"
    assert callable(manifest["material_from_source"])
    assert callable(manifest["artifact_from_output"])
