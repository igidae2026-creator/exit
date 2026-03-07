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
from runtime.profiles import RUNTIME_PROFILES, runtime_profile


def test_runtime_profiles_include_required_scale_targets() -> None:
    smoke = RUNTIME_PROFILES["smoke"]
    soak = RUNTIME_PROFILES["soak"]
    endurance = RUNTIME_PROFILES["endurance"]
    civilization = RUNTIME_PROFILES["civilization"]

    assert smoke.target_ticks == 1000
    assert smoke.worker_min >= 8
    assert smoke.worker_max <= 32

    assert soak.target_ticks == 50000
    assert soak.worker_min >= 64
    assert soak.worker_max >= 256

    assert endurance.target_ticks == 500000
    assert endurance.worker_min >= 256
    assert endurance.worker_max >= 1024

    assert civilization.target_ticks is None


def test_runtime_profile_falls_back_to_smoke() -> None:
    assert runtime_profile("does-not-exist").name == "smoke"
