from __future__ import annotations

from pathlib import Path


def _slug(name: str) -> str:
    return str(name or "").strip().lower().replace("-", "_").replace(" ", "_")


def render_adapter_module(consumer_name: str) -> str:
    slug = _slug(consumer_name)
    return f"""from __future__ import annotations

from typing import Any, Dict


def adapter_manifest() -> Dict[str, Any]:
    return {{
        "adapter_name": "{slug}",
        "contract_version": "1.0.0",
        "material_from_source": material_from_source,
        "artifact_from_output": artifact_from_output,
    }}


def material_from_source(source: Dict[str, Any]) -> Dict[str, Any]:
    return {{
        "material_id": str(source.get("material_id") or "{slug}:source"),
        "quality_score": float(source.get("quality_score", 0.0) or 0.0),
        "scope_fit_score": float(source.get("scope_fit_score", 0.0) or 0.0),
        "risk_score": float(source.get("risk_score", 0.0) or 0.0),
        "metadata": {{"project_type": "{slug}"}},
    }}


def artifact_from_output(output: Dict[str, Any]) -> Dict[str, Any]:
    return {{
        "artifact_id": str(output.get("artifact_id") or "{slug}:artifact"),
        "quality_score": float(output.get("quality_score", 0.0) or 0.0),
        "relevance_score": float(output.get("relevance_score", 0.0) or 0.0),
        "stability_score": float(output.get("stability_score", 0.0) or 0.0),
        "risk_score": float(output.get("risk_score", 0.0) or 0.0),
        "artifact_type": "{slug}",
        "metadata": {{"project_type": "{slug}"}},
    }}
"""


def render_test_module(consumer_name: str) -> str:
    slug = _slug(consumer_name)
    return f"""from metaos.adapters.{slug} import adapter_manifest


def test_{slug}_adapter_manifest_shape():
    manifest = adapter_manifest()

    assert manifest["adapter_name"] == "{slug}"
    assert manifest["contract_version"] == "1.0.0"
    assert callable(manifest["material_from_source"])
    assert callable(manifest["artifact_from_output"])
"""


def render_onboarding_template(consumer_name: str) -> str:
    slug = _slug(consumer_name)
    return f"""# {slug} Consumer Onboarding

1. Implement `metaos/adapters/{slug}.py`
2. Register the adapter through `metaos.runtime.consumer_api.register_consumer`
3. Run consumer conformance
4. Add project-specific source and artifact normalization
5. Confirm version compatibility before rollout
"""


def generate_consumer_scaffold(output_root: str | Path, consumer_name: str) -> dict:
    slug = _slug(consumer_name)
    root = Path(output_root)
    adapter_dir = root / "metaos" / "adapters"
    tests_dir = root / "tests"
    docs_dir = root / "docs" / "runtime"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    adapter_path = adapter_dir / f"{slug}.py"
    test_path = tests_dir / f"test_{slug}_adapter.py"
    doc_path = docs_dir / f"{slug.upper()}_CONSUMER_ONBOARDING.md"

    adapter_path.write_text(render_adapter_module(consumer_name), encoding="utf-8")
    test_path.write_text(render_test_module(consumer_name), encoding="utf-8")
    doc_path.write_text(render_onboarding_template(consumer_name), encoding="utf-8")

    return {
        "consumer_name": slug,
        "adapter_path": str(adapter_path),
        "test_path": str(test_path),
        "doc_path": str(doc_path),
    }
