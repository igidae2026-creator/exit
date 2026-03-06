from kernel.contracts import PRIMARY_ARTIFACT_CLASSES
from kernel.validator import validate_runtime


def test_no_standalone_quota_artifact_class() -> None:
    assert "quota" not in PRIMARY_ARTIFACT_CLASSES
    result = validate_runtime({"artifact_classes": PRIMARY_ARTIFACT_CLASSES, "family_ids": {}, "domain_calls": {"input", "generate", "evaluate", "metrics", "loop"}})
    assert result["ok"] is True

