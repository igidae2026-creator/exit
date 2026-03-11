from metaos.runtime.adapter_conformance import run_adapter_conformance
from metaos.runtime.adapter_migrations import clear_migration_rules, register_migration_rule
from metaos.runtime.adapter_recovery import detect_duplicate_events, replay_resume_decision
from metaos.runtime.adapter_registry import (
    adapter_resolution,
    clear_registered_adapters,
    conformance_matrix,
    register_adapter,
)
from metaos.runtime.adapter_runtime_contracts import CONFORMANCE_CHECKS


def _webnovel_manifest():
    return {
        "adapter_name": "web_novel",
        "contract_version": "1.0.0",
        "material_from_source": lambda source: {
            "material_id": source["material_id"],
            "quality_score": source["quality_score"],
            "scope_fit_score": source["scope_fit_score"],
            "risk_score": source["risk_score"],
        },
        "artifact_from_output": lambda artifact: {
            "artifact_id": artifact["artifact_id"],
            "quality_score": artifact["quality_score"],
            "relevance_score": artifact["relevance_score"],
            "stability_score": artifact["stability_score"],
            "risk_score": artifact["risk_score"],
        },
    }


def _research_manifest():
    return {
        "adapter_name": "research_note",
        "contract_version": "1.0.0",
        "material_from_source": lambda source: {
            "material_id": source["material_id"],
            "quality_score": source["quality_score"],
            "scope_fit_score": source["scope_fit_score"],
            "risk_score": source["risk_score"],
        },
        "artifact_from_output": lambda artifact: {
            "artifact_id": artifact["artifact_id"],
            "quality_score": artifact["quality_score"],
            "relevance_score": artifact["relevance_score"],
            "stability_score": artifact["stability_score"],
            "risk_score": artifact["risk_score"],
        },
    }


def setup_function():
    clear_registered_adapters()
    clear_migration_rules()


def test_missing_adapter_defaults_to_hold():
    result = adapter_resolution("missing_project")

    assert result["verdict"] == "hold"
    assert result["reason"] == "missing_project_adapter"


def test_version_mismatch_rejects():
    register_adapter(
        "broken",
        lambda: {
            "adapter_name": "broken",
            "contract_version": "2.0.0",
            "material_from_source": lambda source: source,
            "artifact_from_output": lambda artifact: artifact,
        },
    )

    result = adapter_resolution("broken")

    assert result["verdict"] == "reject"
    assert result["reason"] == "adapter_contract_version_mismatch"


def test_version_mismatch_with_registered_migration_holds_with_plan():
    register_adapter(
        "migrating",
        lambda: {
            "adapter_name": "migrating",
            "contract_version": "0.9.0",
            "material_from_source": lambda source: source,
            "artifact_from_output": lambda artifact: artifact,
        },
    )
    register_migration_rule(
        "0.9.0",
        "1.0.0",
        strategy="dual_read",
        steps=["freeze rollout", "run migration", "reenable consumer"],
        compatibility_window="one_release",
    )

    result = adapter_resolution("migrating")

    assert result["verdict"] == "hold"
    assert result["reason"] == "migration_required"
    assert result["migration_plan"]["strategy"] == "dual_read"


def test_two_adapters_share_same_conformance_matrix_and_flow():
    register_adapter("web_novel", _webnovel_manifest)
    register_adapter("research_note", _research_manifest)

    rows = conformance_matrix()
    assert len(rows) == 2
    assert all(row["checks_required"] == CONFORMANCE_CHECKS for row in rows)
    assert all("migration_strategy" in row for row in rows)

    webnovel = run_adapter_conformance(
        "web_novel",
        {"material_id": "src:wn", "quality_score": 0.9, "scope_fit_score": 0.85, "risk_score": 0.1},
        {"artifact_id": "art:wn", "quality_score": 0.9, "relevance_score": 0.82, "stability_score": 0.85, "risk_score": 0.1},
    )
    research = run_adapter_conformance(
        "research_note",
        {"material_id": "src:rn", "quality_score": 0.91, "scope_fit_score": 0.83, "risk_score": 0.12},
        {"artifact_id": "art:rn", "quality_score": 0.89, "relevance_score": 0.84, "stability_score": 0.81, "risk_score": 0.1},
    )

    assert webnovel["ok"] is True
    assert research["ok"] is True
    assert webnovel["promotion_decision"]["verdict"] == "promote"
    assert research["promotion_decision"]["verdict"] == "promote"


def test_recovery_guardrails_detect_duplicates_and_resume_consistency():
    duplicates = detect_duplicate_events(
        [
            {"ts": "2026-03-11 11:00:00", "type": "scope_evaluate", "payload": {"material_id": "x"}},
            {"ts": "2026-03-11 11:00:00", "type": "scope_evaluate", "payload": {"material_id": "x"}},
        ]
    )
    decision = replay_resume_decision(
        [{"ts": "2026-03-11 11:00:00", "type": "scope_evaluate", "payload": {"material_id": "x"}}],
        {"queue_status": "running", "jobs": [], "current_index": 2},
        {"current_index": 2},
        ["queue_status", "jobs"],
    )

    assert len(duplicates) == 1
    assert decision["verdict"] == "resume"
