from __future__ import annotations

from typing import Any, Dict


def adapter_manifest() -> Dict[str, Any]:
    return {
        "adapter_name": "analytics_dash",
        "contract_version": "1.0.0",
        "material_from_source": material_from_source,
        "artifact_from_output": artifact_from_output,
    }


def material_from_source(source: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "material_id": str(source.get("material_id") or "analytics:unknown"),
        "quality_score": float(source.get("quality_score", 0.0) or 0.0),
        "scope_fit_score": float(source.get("scope_fit_score", 0.0) or 0.0),
        "risk_score": float(source.get("risk_score", 0.0) or 0.0),
        "metadata": {"dashboard_type": source.get("dashboard_type", "analytics")},
    }


def artifact_from_output(output: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "artifact_id": str(output.get("artifact_id") or "analytics-artifact:unknown"),
        "quality_score": float(output.get("quality_score", 0.0) or 0.0),
        "relevance_score": float(output.get("relevance_score", 0.0) or 0.0),
        "stability_score": float(output.get("stability_score", 0.0) or 0.0),
        "risk_score": float(output.get("risk_score", 0.0) or 0.0),
        "artifact_type": "analytics_dash",
        "metadata": {"panel_count": int(output.get("panel_count", 0) or 0)},
    }
