from metaos.adapters.release_notes import adapter_manifest


def test_release_notes_adapter_manifest_shape():
    manifest = adapter_manifest()

    assert manifest["adapter_name"] == "release_notes"
    assert manifest["contract_version"] == "1.0.0"
    assert callable(manifest["material_from_source"])
    assert callable(manifest["artifact_from_output"])
