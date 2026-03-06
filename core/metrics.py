from __future__ import annotations

import datetime as dt
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


def _utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _entropy_normalized(items: list[str]) -> float:
    if not items:
        return 0.0
    total = len(items)
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    if len(counts) == 1:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log(p)
    max_entropy = math.log(len(counts))
    if max_entropy <= 0:
        return 0.0
    return _clamp01(entropy / max_entropy)


def _append_jsonl_atomic(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


@dataclass(slots=True)
class MetricsEngine:
    """Compute normalized METAOS metrics and append them to metrics.jsonl."""

    output_path: Path | str = Path("data/metrics.jsonl")

    def evaluate(self, context: Mapping[str, Any]) -> dict[str, float]:
        quality = self._quality(context)
        novelty = self._novelty(context)
        diversity = self._diversity(context)
        efficiency = self._efficiency(context)
        cost = self._cost(context)

        score = _clamp01(
            (0.30 * quality)
            + (0.20 * novelty)
            + (0.20 * diversity)
            + (0.20 * efficiency)
            + (0.10 * cost)
        )

        metrics = {
            "quality": round(quality, 6),
            "novelty": round(novelty, 6),
            "diversity": round(diversity, 6),
            "efficiency": round(efficiency, 6),
            "cost": round(cost, 6),
            "score": round(score, 6),
        }

        record = {
            "timestamp": _utc_timestamp(),
            "event_type": "metrics",
            "payload": metrics,
        }
        _append_jsonl_atomic(Path(self.output_path), record)
        return metrics

    def _quality(self, context: Mapping[str, Any]) -> float:
        if "quality" in context:
            return _clamp01(_to_float(context.get("quality")))
        signal = _clamp01(_to_float(context.get("signal_strength"), 0.0))
        success = _clamp01(_to_float(context.get("success_rate"), 0.0))
        feedback = _clamp01(_to_float(context.get("feedback_score"), 0.0))
        return _clamp01((0.5 * success) + (0.3 * signal) + (0.2 * feedback))

    def _novelty(self, context: Mapping[str, Any]) -> float:
        if "novelty" in context:
            return _clamp01(_to_float(context.get("novelty")))
        is_new = _clamp01(_to_float(context.get("is_new"), 0.0))
        unique_ratio = _clamp01(_to_float(context.get("unique_ratio"), 0.0))
        distance = _clamp01(_to_float(context.get("distance_from_prior"), 0.0))
        return _clamp01((0.4 * unique_ratio) + (0.4 * distance) + (0.2 * is_new))

    def _diversity(self, context: Mapping[str, Any]) -> float:
        if "diversity" in context:
            return _clamp01(_to_float(context.get("diversity")))

        categories = context.get("categories")
        if isinstance(categories, list):
            values = [str(x) for x in categories if x is not None]
            if values:
                return _entropy_normalized(values)

        cohort_ratio = _clamp01(_to_float(context.get("cohort_ratio"), 0.0))
        source_mix = _clamp01(_to_float(context.get("source_mix"), 0.0))
        return _clamp01((0.6 * cohort_ratio) + (0.4 * source_mix))

    def _efficiency(self, context: Mapping[str, Any]) -> float:
        if "efficiency" in context:
            return _clamp01(_to_float(context.get("efficiency")))

        throughput = _clamp01(_to_float(context.get("throughput"), 0.0))
        latency_ms = max(0.0, _to_float(context.get("latency_ms"), 0.0))
        latency_target_ms = max(1.0, _to_float(context.get("latency_target_ms"), 1000.0))
        latency_score = _clamp01(1.0 - (latency_ms / latency_target_ms))
        return _clamp01((0.5 * throughput) + (0.5 * latency_score))

    def _cost(self, context: Mapping[str, Any]) -> float:
        if "cost" in context:
            return _clamp01(_to_float(context.get("cost")))

        spend = max(0.0, _to_float(context.get("spend_usd"), 0.0))
        budget = max(0.01, _to_float(context.get("budget_usd"), 1.0))
        budget_utilization = _clamp01(spend / budget)
        # Lower spend is better for cost score.
        return _clamp01(1.0 - budget_utilization)


def evaluate_metrics(context: Mapping[str, Any], output_path: str | Path = "metrics.jsonl") -> dict[str, float]:
    """Convenience function for one-shot metric evaluation + persistence."""

    engine = MetricsEngine(output_path=output_path)
    return engine.evaluate(context)
