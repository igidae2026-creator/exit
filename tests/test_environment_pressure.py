import os
import tempfile

from runtime.environment_pressure import ingest_environment_signals, latest_environment_signals
from runtime.pressure_derivation import pressure_frame


def test_environment_pressure_enters_as_append_only_artifact_and_affects_pressure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["METAOS_ROOT"] = tmp
        try:
            row = ingest_environment_signals(
                {
                    "competition_pressure": 0.8,
                    "market_adoption_pressure": 0.7,
                    "platform_policy_pressure": 0.5,
                    "audience_feedback_pressure": 0.6,
                    "environment_volatility": 0.9,
                },
                tick=5,
            )
            latest = latest_environment_signals([row])
            derived = pressure_frame(
                {
                    "artifact_population": {"output": 4},
                    "lineage_population": {"a": 4},
                    "domain_population": {"alpha": 4},
                    "policy_population": {"generations": 1},
                    "knowledge_density": 0.2,
                    "memory_growth": 0.2,
                    "exploration_budget": 3,
                },
                recent_truth=[{"signals": latest}],
            )
            assert row["artifact_id"]
            assert derived["competition_pressure"] == 0.8
            assert derived["environment_volatility"] == 0.9
            assert derived["domain_shift_pressure"] > 0.0
        finally:
            os.environ.pop("METAOS_ROOT", None)
