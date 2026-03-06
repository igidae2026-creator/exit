from validation.constitution import validate_constitution


def test_constitution_guard_rejects_quota_artifact_class() -> None:
    assert validate_constitution({"artifact_classes": {"quota"}})["ok"] is False
