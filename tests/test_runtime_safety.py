import runtime.runtime_safety as runtime_safety_module
from runtime.runtime_safety import runtime_safety


def test_runtime_safety_exposes_pressure_and_actions() -> None:
    out = runtime_safety()
    assert set(out) >= {"storage_pressure", "runtime_pressure", "archive_pressure", "safety_actions"}


def test_runtime_safety_prefers_active_ecology_counts(monkeypatch) -> None:
    monkeypatch.setattr(runtime_safety_module, "replay_state", lambda: {"tick": 1})
    monkeypatch.setattr(
        runtime_safety_module,
        "civilization_state",
        lambda: {
            "active_lineage_count": 8,
            "active_domain_count": 4,
            "lineage_counts": {"legacy": 1},
            "domain_distribution": {"legacy": 1.0},
            "active_domain_distribution": {"alpha": 0.4, "beta": 0.3, "gamma": 0.2, "delta": 0.1},
            "economy_balance_score": 0.7,
            "stability_score": 0.8,
            "drift_score": 0.1,
            "stagnation_score": 0.1,
            "overexpansion_score": 0.0,
            "underexploration_score": 0.0,
        },
    )
    monkeypatch.setattr(runtime_safety_module, "pressure_frame", lambda _: {"repair_pressure": 0.1})
    monkeypatch.setattr(runtime_safety_module, "federation_state", lambda: {})
    monkeypatch.setattr(runtime_safety_module, "ecosystem_state", lambda: {})
    monkeypatch.setattr(
        runtime_safety_module,
        "self_tuning_guardrails",
        lambda *_args, **_kwargs: {"guardrail_actions": [], "federation_safety_actions": [], "guardrail_state": {}, "tuned_thresholds": {}},
    )

    out = runtime_safety(profile="smoke")

    assert out["surviving_lineages"] == 8
    assert out["active_domains"] == 4
