from __future__ import annotations

from typing import Any, Mapping

from artifact.registry import register_envelope
from kernel.contracts import POLICY_FAMILIES


def propose_policy_bundle(family_ids: Mapping[str, str], *, parent: str | None = None) -> str:
    normalized = {name: str(family_ids.get(name, "")) for name in POLICY_FAMILIES}
    refs = {"parents": [parent] if parent else [], "inputs": [], "subjects": [], "context": {}}
    return register_envelope(
        aclass="policy",
        atype="policy_bundle",
        spec={"family_ids": normalized},
        refs=refs,
        provenance={"activation_unit": "bundle"},
        constraints={"tick_boundary_only": True},
    )

