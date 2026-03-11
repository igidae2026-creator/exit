from pathlib import Path
import sys

from metaos.adapters.analytics_dash import adapter_manifest as analytics_manifest
from metaos.adapters.code_patch import adapter_manifest as code_patch_manifest
from metaos.adapters.research_note import adapter_manifest as research_manifest
from metaos.runtime.consumer_api import (
    consumer_matrix,
    register_consumer,
    register_consumer_migration,
    reset_consumers,
    resolve_consumer,
    run_consumer_conformance,
)


def _load_webnovel_manifest():
    webnovel_root = Path("/home/meta_os/web_novel")
    if str(webnovel_root) not in sys.path:
        sys.path.insert(0, str(webnovel_root))
    from engine.metaos_consumer_bridge import adapter_manifest

    return adapter_manifest


def setup_function():
    reset_consumers()


def test_webnovel_consumer_reconnects_to_metaos_core():
    register_consumer("web_novel", _load_webnovel_manifest())

    result = run_consumer_conformance(
        "web_novel",
        {
            "project": {"platform": "Munpia", "genre_bucket": "A"},
            "track": {"id": "munpia_a"},
            "material_id": "src:munpia_a",
            "quality_score": 0.9,
            "scope_fit_score": 0.84,
            "risk_score": 0.12,
        },
        {
            "cfg": {
                "project": {"name": "consumer-check", "platform": "Munpia", "genre_bucket": "A"},
                "output": {"root_dir": "/tmp/metaos-consumer-outputs"},
            },
            "episode_result": {
                "episode": 9,
                "predicted_retention": 0.9,
                "quality_score": 0.84,
                "quality_gate": {"passed": True, "failed_checks": []},
                "story_state": {"world": {"instability": 3}},
            },
        },
    )

    assert result["ok"] is True
    assert result["scope_decision"]["verdict"] == "accept"
    assert result["promotion_decision"]["verdict"] == "promote"


def test_two_real_consumers_share_same_contracts_and_matrix():
    register_consumer("web_novel", _load_webnovel_manifest())
    register_consumer("research_note", research_manifest)

    rows = consumer_matrix()

    assert len(rows) == 2
    assert {row["project_type"] for row in rows} == {"web_novel", "research_note"}
    assert all(row["status"] == "ready" for row in rows)
    assert {row["project_type"]: row["consumer_family"] for row in rows} == {
        "web_novel": "creative_production",
        "research_note": "knowledge_dense_review",
    }
    assert {row["project_type"]: row["default_profile"] for row in rows} == {
        "web_novel": "balanced",
        "research_note": "conservative",
    }

    research = run_consumer_conformance(
        "research_note",
        {
            "material_id": "src:research_1",
            "quality_score": 0.92,
            "scope_fit_score": 0.81,
            "risk_score": 0.15,
            "domain": "research",
            "topic": "battery",
        },
        {
            "artifact_id": "artifact:research_1",
            "quality_score": 0.9,
            "relevance_score": 0.88,
            "stability_score": 0.81,
            "risk_score": 0.12,
            "citation_count": 8,
        },
    )

    assert research["ok"] is True
    assert research["promotion_decision"]["verdict"] == "promote"


def test_four_real_consumers_share_same_matrix_without_contract_changes():
    register_consumer("web_novel", _load_webnovel_manifest())
    register_consumer("research_note", research_manifest)
    register_consumer("analytics_dash", analytics_manifest)
    register_consumer("code_patch", code_patch_manifest)

    rows = consumer_matrix()

    assert len(rows) == 4
    assert {row["project_type"] for row in rows} == {"web_novel", "research_note", "analytics_dash", "code_patch"}
    assert all(row["status"] == "ready" for row in rows)


def test_consumer_resolution_enters_hold_when_migration_rule_exists():
    register_consumer(
        "legacy_note",
        lambda: {
            "adapter_name": "legacy_note",
            "contract_version": "0.8.0",
            "material_from_source": lambda source: source,
            "artifact_from_output": lambda artifact: artifact,
        },
    )
    register_consumer_migration(
        "0.8.0",
        "1.0.0",
        strategy="rewrite_then_replay",
        steps=["disable writes", "migrate manifests", "replay snapshots"],
    )

    resolution = resolve_consumer("legacy_note")

    assert resolution["verdict"] == "hold"
    assert resolution["reason"] == "migration_required"
    assert resolution["migration_plan"]["strategy"] == "rewrite_then_replay"
