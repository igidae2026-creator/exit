import os
import tempfile

from federation.federation_state import append_federation_row
from runtime.runtime_safety import runtime_safety


def test_federation_safety_detects_bounded_overload_conditions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        os.environ["METAOS_FEDERATION_ENABLED"] = "1"
        try:
            for index in range(10):
                append_federation_row("artifact_exchange", {"artifact_id": f"a{index}"})
                append_federation_row("domain_propagation", {"domain": f"d{index}"})
            for index in range(520):
                append_federation_row("knowledge_exchange", {"summary": {"k": index}})
            safety = runtime_safety()
            assert any(name in safety["safety_actions"] for name in ("artifact_flood", "domain_explosion", "policy_cascade", "federation_overload"))
        finally:
            os.environ.pop("METAOS_ROOT", None)
            os.environ.pop("METAOS_FEDERATION_ENABLED", None)
