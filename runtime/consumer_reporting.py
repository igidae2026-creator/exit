from __future__ import annotations

import json
import os
import importlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable


def _root() -> Path:
    root = os.environ.get("METAOS_ROOT")
    if root:
        return Path(root)
    return Path("/tmp/metaos_runtime")


def consumer_ledger_path() -> Path:
    path = _root() / "data" / "consumer_runtime.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def append_consumer_record(record_type: str, payload: Dict[str, Any]) -> dict[str, Any]:
    row = {"record_type": str(record_type), "payload": dict(payload)}
    data = json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n"
    path = consumer_ledger_path()
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return row


def read_consumer_records() -> list[dict[str, Any]]:
    path = consumer_ledger_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def clear_consumer_records() -> None:
    path = consumer_ledger_path()
    if path.exists():
        path.unlink()


def _verdict_records(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("record_type") in {"consumer_resolution", "consumer_conformance"}]


def consumer_operating_report() -> Dict[str, Any]:
    rows = read_consumer_records()
    verdict_rows = _verdict_records(rows)
    verdict_counter: Counter[str] = Counter()
    hold_reasons: Counter[str] = Counter()
    reject_reasons: Counter[str] = Counter()
    escalate_reasons: Counter[str] = Counter()
    health_rollup: dict[str, dict[str, Any]] = defaultdict(lambda: {"verdicts": Counter(), "reasons": Counter()})

    for row in verdict_rows:
        payload = dict(row.get("payload") or {})
        project_type = str(payload.get("project_type") or "unknown")
        verdict = str(payload.get("verdict") or "unknown")
        reason = str(payload.get("reason") or "unknown")
        verdict_counter[verdict] += 1
        health_rollup[project_type]["verdicts"][verdict] += 1
        health_rollup[project_type]["reasons"][reason] += 1
        if verdict == "hold":
            hold_reasons[reason] += 1
        elif verdict == "reject":
            reject_reasons[reason] += 1
        elif verdict == "escalate":
            escalate_reasons[reason] += 1

    migration_queue = [
        row.get("payload", {})
        for row in rows
        if row.get("record_type") == "consumer_migration"
    ]
    health_rows = []
    for project_type, summary in sorted(health_rollup.items()):
        total = sum(summary["verdicts"].values()) or 1
        health_rows.append(
            {
                "project_type": project_type,
                "total_decisions": total,
                "accept_rate": summary["verdicts"].get("accept", 0) / total,
                "hold_rate": summary["verdicts"].get("hold", 0) / total,
                "reject_rate": summary["verdicts"].get("reject", 0) / total,
                "escalate_rate": summary["verdicts"].get("escalate", 0) / total,
                "top_reason": summary["reasons"].most_common(1)[0][0] if summary["reasons"] else None,
            }
        )

    return {
        "verdict_distribution": dict(verdict_counter),
        "hold_top_reasons": hold_reasons.most_common(5),
        "reject_top_patterns": reject_reasons.most_common(5),
        "escalate_rate": verdict_counter.get("escalate", 0) / max(1, sum(verdict_counter.values())),
        "migration_queue": migration_queue,
        "consumer_health_rollup": health_rows,
        "conformance_matrix": _conformance_matrix(),
        "default_profile_mapping": _default_profile_mapping(),
    }


__all__ = [
    "append_consumer_record",
    "clear_consumer_records",
    "consumer_ledger_path",
    "consumer_operating_report",
    "read_consumer_records",
]


def _conformance_matrix() -> list[dict]:
    module = importlib.import_module("metaos" + ".runtime.adapter_registry")
    return module.conformance_matrix()


def _default_profile_mapping() -> dict[str, str]:
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    registry = importlib.import_module("metaos" + ".runtime.adapter_registry")
    mapping: dict[str, str] = {}
    for project_type in sorted(getattr(registry, "_REGISTRY", {}).keys()):
        mapping[str(project_type)] = str(module.default_profile_for_consumer(project_type))
    return mapping
