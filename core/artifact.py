import os
import uuid


def write_artifact():
    artifact_id = str(uuid.uuid4())
    path = f"artifact_store/{artifact_id}"

    os.makedirs(path, exist_ok=True)

    with open(f"{path}/artifact.txt", "w") as f:
        f.write("artifact generated")

    return artifact_id
