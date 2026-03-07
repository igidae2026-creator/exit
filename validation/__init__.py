__all__ = ["validate_artifact_classes"]


def validate_artifact_classes(payload):
    from validation.artifacts import validate_artifact_classes as _validate_artifact_classes

    return _validate_artifact_classes(payload)
