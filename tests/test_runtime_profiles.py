from runtime.long_run_validation import PROFILE_TABLE, validate_long_run
from runtime.orchestrator import OrchestratorConfig


def test_orchestrator_config_defaults_to_unbounded_mode() -> None:
    config = OrchestratorConfig()
    assert config.max_ticks is None


def test_long_run_validation_uses_profile_minimums() -> None:
    out = validate_long_run(profile="smoke", ticks=64, seed=11, fail_open=False)
    assert out["profile"] == "smoke"
    assert out["ticks"] >= PROFILE_TABLE["smoke"].min_ticks
    assert out["profile_requirements"]["ticks"] == PROFILE_TABLE["smoke"].min_ticks
    assert isinstance(out["threshold_checks"], dict)
    assert "replay_ok" in out["threshold_checks"]
