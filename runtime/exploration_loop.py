from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Mapping

from artifact.archive import save
from artifact.registry import register_envelope
from genesis.spine import append_event, append_metrics


def _call(source: Any, name: str, *args: Any, default: Any = None) -> Any:
    value = getattr(source, name, None)
    if callable(value):
        return value(*args)
    if isinstance(source, Mapping) and callable(source.get(name)):
        return source[name](*args)
    return default


def _safe_shutdown(source: Any, tick: int) -> bool:
    probe = getattr(source, "safe_shutdown", None)
    if callable(probe):
        return bool(probe(tick))
    if isinstance(source, Mapping) and callable(source.get("safe_shutdown")):
        return bool(source["safe_shutdown"](tick))
    return False


def run_loop(signal_source: Any) -> Iterator[dict[str, Any]]:
    tick = 0
    while True:
        if _safe_shutdown(signal_source, tick):
            return
        tick += 1
        signal = _call(signal_source, "signal", tick, default={"tick": tick})
        generated = _call(signal_source, "generate", signal, default={"signal": signal, "candidate": tick})
        evaluation = _call(signal_source, "evaluate", generated, default={"score": 1.0, "valid": True})
        selected = _call(signal_source, "select", generated, evaluation, default={"artifact": generated, "score": evaluation.get("score", 1.0)})
        mutated = _call(signal_source, "mutate", selected, default=dict(selected))
        archived = _call(signal_source, "archive", mutated, default=mutated)
        payload = {
            "tick": tick,
            "signal": signal,
            "generate": generated,
            "evaluate": evaluation,
            "select": selected,
            "mutate": mutated,
            "archive": archived,
        }
        append_event("loop_tick", {"tick": tick, "signal": signal})
        append_metrics({"tick": tick, "score": float(evaluation.get("score", 0.0)), "quest": {"type": "exploration"}, "routing": {"selected_domain": "default"}})
        register_envelope(
            aclass="output",
            atype="loop_artifact",
            spec={"payload": payload},
            provenance={"score": float(evaluation.get("score", 0.0))},
        )
        save("loop_archive", payload)
        yield payload


__all__ = ["run_loop"]
