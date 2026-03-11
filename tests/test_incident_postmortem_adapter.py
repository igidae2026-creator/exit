from metaos.adapters.incident_postmortem import adapter_manifest


def test_incident_postmortem_adapter_manifest_shape():
    manifest = adapter_manifest()

    assert manifest["adapter_name"] == "incident_postmortem"
    assert manifest["contract_version"] == "1.0.0"
    assert callable(manifest["material_from_source"])
    assert callable(manifest["artifact_from_output"])
