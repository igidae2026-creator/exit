from __future__ import annotations

from typing import Any, Mapping, Sequence

from runtime.signal_truth import append_signal, signal_state, transition_signal


def signal_sources(history: Sequence[Mapping[str, Any]] | None = None, metrics: Mapping[str, Any] | None = None, *, data_dir: str = "data") -> dict[str, Any]:
    rows = list(history or [])
    state = signal_state(data_dir=data_dir)
    return {
        "history": rows[-64:],
        "metrics": dict(metrics or {}),
        "signals": state,
    }


def ingest_signal(payload: Mapping[str, Any], *, data_dir: str = "data") -> dict[str, Any]:
    row = append_signal(payload, data_dir=data_dir)
    transition_signal(str(row["id"]), "queued", data_dir=data_dir)
    return row


def consume_signal(signal_id: str, *, consumer: str, data_dir: str = "data") -> dict[str, Any]:
    return transition_signal(signal_id, "consumed", consumed_by=consumer, data_dir=data_dir)
