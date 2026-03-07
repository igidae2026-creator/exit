from __future__ import annotations

from typing import Any, Mapping, Sequence

from artifact.archive import append_archive, archive_window, latest_archive
from artifact.registry import register_envelope
from genesis.spine import append_event


ENVIRONMENT_SIGNAL_KEYS = (
    "competition_pressure",
    "market_adoption_pressure",
    "platform_policy_pressure",
    "audience_feedback_pressure",
    "environment_volatility",
)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def normalize_environment_signals(signals: Mapping[str, Any]) -> dict[str, float]:
    return {key: _clamp(float(signals.get(key, 0.0) or 0.0)) for key in ENVIRONMENT_SIGNAL_KEYS}


def ingest_environment_signals(
    signals: Mapping[str, Any],
    *,
    tick: int | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_environment_signals(signals)
    payload = {
        "signals": normalized,
        "tick": int(tick or 0),
        "context": dict(context or {}),
    }
    artifact_id = register_envelope(
        aclass="evaluation",
        atype="environment_signal",
        spec=payload,
        provenance={
            "score": sum(normalized.values()) / max(1, len(normalized)),
            "novelty": normalized["competition_pressure"],
            "diversity": normalized["audience_feedback_pressure"],
            "efficiency": 1.0 - normalized["environment_volatility"],
            "repair": normalized["platform_policy_pressure"],
        },
        refs={"parents": [], "inputs": [], "subjects": ["environment"], "context": dict(context or {})},
        constraints={"append_only_truth": True, "external_signal": True},
    )
    row = {"artifact_id": artifact_id, **payload}
    append_archive("environment_signal", row)
    from runtime.civilization_memory import remember

    remember("environment_signal", row)
    append_event("environment_pressure_signal", row)
    return row


def latest_environment_signals(history: Sequence[Mapping[str, Any]] | None = None) -> dict[str, float]:
    rows = list(history or [])
    for row in reversed(rows):
        if isinstance(row.get("signals"), Mapping):
            return normalize_environment_signals(dict(row["signals"]))
        archive_signals = row.get("environment_signals")
        if isinstance(archive_signals, Mapping):
            return normalize_environment_signals(dict(archive_signals))
    latest = latest_archive("environment_signal", {})
    if isinstance(latest, Mapping):
        signals = latest.get("signals", latest)
        if isinstance(signals, Mapping):
            return normalize_environment_signals(signals)
    return {key: 0.0 for key in ENVIRONMENT_SIGNAL_KEYS}


def environment_signal_window(limit: int = 32) -> list[dict[str, Any]]:
    rows = archive_window(limit=limit, kinds={"environment_signal"})
    return [dict(row.get("payload", row)) for row in rows if isinstance(row, Mapping)]


__all__ = [
    "ENVIRONMENT_SIGNAL_KEYS",
    "environment_signal_window",
    "ingest_environment_signals",
    "latest_environment_signals",
    "normalize_environment_signals",
]
