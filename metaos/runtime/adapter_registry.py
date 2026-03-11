from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from metaos.runtime.adapter_migrations import migration_plan
from metaos.runtime.adapter_runtime_contracts import RUNTIME_CONTRACT_VERSION, compatibility_report


AdapterFactory = Callable[[], Dict[str, Any]]
_REGISTRY: Dict[str, AdapterFactory] = {}


def register_adapter(project_type: str, factory: AdapterFactory) -> None:
    _REGISTRY[str(project_type)] = factory


def clear_registered_adapters() -> None:
    _REGISTRY.clear()


def get_adapter_manifest(project_type: str) -> Optional[Dict[str, Any]]:
    factory = _REGISTRY.get(str(project_type))
    return factory() if factory else None


def adapter_resolution(project_type: str) -> Dict[str, Any]:
    manifest = get_adapter_manifest(project_type)
    if not manifest:
        return {
            "status": "missing",
            "project_type": project_type,
            "verdict": "hold",
            "reason": "missing_project_adapter",
        }
    adapter_version = str(manifest.get("contract_version") or "")
    report = compatibility_report(RUNTIME_CONTRACT_VERSION, adapter_version)
    if not report["compatible"]:
        plan = migration_plan(adapter_version, RUNTIME_CONTRACT_VERSION)
        if plan["available"]:
            return {
                "status": "migration_pending",
                "project_type": project_type,
                "verdict": "hold",
                "reason": "migration_required",
                "compatibility": report,
                "migration_plan": plan,
                "adapter_manifest": manifest,
            }
        return {
            "status": "incompatible",
            "project_type": project_type,
            "verdict": "reject",
            "reason": "adapter_contract_version_mismatch",
            "compatibility": report,
            "adapter_manifest": manifest,
        }
    return {
        "status": "ready",
        "project_type": project_type,
        "verdict": "accept",
        "reason": "adapter_ready",
        "compatibility": report,
        "adapter_manifest": manifest,
    }


def conformance_matrix() -> list[dict]:
    from metaos.runtime.adapter_runtime_contracts import CONFORMANCE_CHECKS

    rows = []
    for project_type in sorted(_REGISTRY):
        resolution = adapter_resolution(project_type)
        rows.append(
            {
                "project_type": project_type,
                "adapter_name": (resolution.get("adapter_manifest") or {}).get("adapter_name"),
                "status": resolution.get("status"),
                "verdict": resolution.get("verdict"),
                "reason": resolution.get("reason"),
                "contract_version": (resolution.get("adapter_manifest") or {}).get("contract_version"),
                "migration_strategy": ((resolution.get("migration_plan") or {}).get("strategy")),
                "checks_required": list(CONFORMANCE_CHECKS),
            }
        )
    return rows
