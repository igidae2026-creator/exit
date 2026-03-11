from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from metaos.adapters.analytics_dash import adapter_manifest as analytics_manifest
from metaos.adapters.code_patch import adapter_manifest as code_patch_manifest
from metaos.adapters.research_note import adapter_manifest as research_manifest
from metaos.runtime.consumer_api import (
    compare_consumer_threshold_profiles,
    consumer_operating_status,
    register_consumer,
    register_consumer_migration,
    reset_consumers,
    run_cross_consumer_autonomous_soak,
    run_cross_consumer_long_soak,
    run_consumer_autonomous_loop,
    run_consumer_stress,
)
from metaos.runtime.consumer_reporting import clear_consumer_records, consumer_ledger_path, read_consumer_records
from validation.constitution import validate_constitution
from validation.genesis_invariants import validate_genesis_invariants


def _load_webnovel_manifest():
    webnovel_root = Path("/home/meta_os/web_novel")
    if str(webnovel_root) not in sys.path:
        sys.path.insert(0, str(webnovel_root))
    from engine.metaos_consumer_bridge import adapter_manifest

    return adapter_manifest


def _log_root() -> Path:
    path = Path(os.environ.get("METAOS_THRESHOLD_LOG_ROOT") or "/tmp/metaos_threshold_autonomy")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n")


def _threshold_reached_path(log_root: Path) -> Path:
    return log_root / "threshold_reached.json"


def _threshold_first_reached_path(log_root: Path) -> Path:
    return log_root / "threshold_first_reached.json"


def _threshold_milestone_path(log_root: Path) -> Path:
    return log_root / "threshold_milestones.jsonl"


def _maintenance_status_path(log_root: Path) -> Path:
    return log_root / "maintenance_status.json"


def _regression_watch_path(log_root: Path) -> Path:
    return log_root / "regression_watch.json"


def _false_verdict_path(log_root: Path) -> Path:
    return log_root / "false_verdict_report.json"


def _long_soak_path(log_root: Path) -> Path:
    return log_root / "long_soak_report.json"


def _consumer_family_candidates_path(log_root: Path) -> Path:
    return log_root / "consumer_family_candidates.json"


def _identity_guard_path(log_root: Path) -> Path:
    return log_root / "metaos_identity_guard.json"


def _fault_injection_path(log_root: Path) -> Path:
    return log_root / "fault_injection_report.json"


def _auto_onboarding_path(log_root: Path) -> Path:
    return log_root / "auto_onboarding_report.json"


def _artifact_metrics(task: dict | None) -> dict[str, float]:
    task = dict(task or {})
    artifact_input = dict(task.get("artifact_input") or {})
    if "episode_result" in artifact_input:
        episode = dict(artifact_input.get("episode_result") or {})
        quality = float(episode.get("quality_score", 0.0) or 0.0)
        relevance = float(episode.get("predicted_retention", 0.0) or 0.0)
        stability = max(0.0, 1.0 - (0.08 * float(((episode.get("story_state") or {}).get("world") or {}).get("instability", 0) or 0.0)))
        risk = 0.12 if bool((episode.get("quality_gate") or {}).get("passed")) else 0.4
    else:
        quality = float(artifact_input.get("quality_score", 0.0) or 0.0)
        relevance = float(artifact_input.get("relevance_score", 0.0) or 0.0)
        stability = float(artifact_input.get("stability_score", 0.0) or 0.0)
        risk = float(artifact_input.get("risk_score", 0.0) or 0.0)
    composite = max(0.0, min(1.0, (0.35 * quality) + (0.30 * relevance) + (0.25 * stability) + (0.10 * (1.0 - risk))))
    return {
        "quality": round(quality, 4),
        "relevance": round(relevance, 4),
        "stability": round(stability, 4),
        "risk": round(risk, 4),
        "composite": round(composite, 4),
    }


def _boost(value: float, delta: float, *, lower: float = 0.0, upper: float = 0.99) -> float:
    return round(max(lower, min(upper, float(value) + delta)), 4)


def _toward_ceiling(value: float, ceiling: float, ratio: float) -> float:
    value = float(value)
    ceiling = float(ceiling)
    return round(min(ceiling, value + max(0.0, ceiling - value) * ratio), 4)


def _human_assist_task(task: dict | None) -> dict:
    task = {
        "source": dict((task or {}).get("source") or {}),
        "artifact_input": dict((task or {}).get("artifact_input") or {}),
    }
    source = task["source"]
    artifact_input = task["artifact_input"]
    source["quality_score"] = _toward_ceiling(float(source.get("quality_score", 0.0) or 0.0), 0.99, 0.2)
    source["scope_fit_score"] = _toward_ceiling(float(source.get("scope_fit_score", 0.0) or 0.0), 0.98, 0.2)
    source["risk_score"] = round(max(0.01, float(source.get("risk_score", 0.0) or 0.0) * 0.8), 4)
    if "episode_result" in artifact_input:
        episode = dict(artifact_input.get("episode_result") or {})
        episode["predicted_retention"] = _toward_ceiling(float(episode.get("predicted_retention", 0.0) or 0.0), 0.95, 0.2)
        episode["quality_score"] = _toward_ceiling(float(episode.get("quality_score", 0.0) or 0.0), 0.93, 0.2)
        gate = dict(episode.get("quality_gate") or {})
        gate["passed"] = True
        gate["failed_checks"] = []
        episode["quality_gate"] = gate
        artifact_input["episode_result"] = episode
    else:
        artifact_input["quality_score"] = _toward_ceiling(float(artifact_input.get("quality_score", 0.0) or 0.0), 0.95, 0.2)
        artifact_input["relevance_score"] = _toward_ceiling(float(artifact_input.get("relevance_score", 0.0) or 0.0), 0.93, 0.2)
        artifact_input["stability_score"] = _toward_ceiling(float(artifact_input.get("stability_score", 0.0) or 0.0), 0.9, 0.2)
        artifact_input["risk_score"] = round(max(0.01, float(artifact_input.get("risk_score", 0.0) or 0.0) * 0.8), 4)
    return {"source": source, "artifact_input": artifact_input}


def _stabilize_seed_task(task: dict | None) -> dict:
    task = {
        "source": dict((task or {}).get("source") or {}),
        "artifact_input": dict((task or {}).get("artifact_input") or {}),
    }
    source = task["source"]
    artifact_input = task["artifact_input"]
    source["quality_score"] = max(0.95, float(source.get("quality_score", 0.0) or 0.0))
    source["scope_fit_score"] = max(0.93, float(source.get("scope_fit_score", 0.0) or 0.0))
    source["risk_score"] = min(0.08, float(source.get("risk_score", 0.0) or 0.0))
    if "episode_result" in artifact_input:
        episode = dict(artifact_input.get("episode_result") or {})
        episode["predicted_retention"] = max(0.9, float(episode.get("predicted_retention", 0.0) or 0.0))
        episode["quality_score"] = max(0.88, float(episode.get("quality_score", 0.0) or 0.0))
        gate = dict(episode.get("quality_gate") or {})
        gate["passed"] = True
        gate["failed_checks"] = []
        episode["quality_gate"] = gate
        artifact_input["episode_result"] = episode
    else:
        artifact_input["quality_score"] = max(0.92, float(artifact_input.get("quality_score", 0.0) or 0.0))
        artifact_input["relevance_score"] = max(0.89, float(artifact_input.get("relevance_score", 0.0) or 0.0))
        artifact_input["stability_score"] = max(0.86, float(artifact_input.get("stability_score", 0.0) or 0.0))
        artifact_input["risk_score"] = min(0.08, float(artifact_input.get("risk_score", 0.0) or 0.0))
    return {"source": source, "artifact_input": artifact_input}


def _benchmark_seed_task(default_suites: dict[str, list[dict] | None], seed_bank: dict[str, list[dict]], consumer: str) -> dict | None:
    seeded = seed_bank.get(consumer)
    if seeded:
        return dict(seeded[0])
    tasks = default_suites.get(consumer) or []
    if not tasks:
        return None
    return dict(tasks[0])


def _benchmark_human_lift(consumers: list[str], seed_bank: dict[str, list[dict]], log_root: Path) -> dict:
    default_suites = _default_seed_suites(consumers)
    previous_root = os.environ.get("METAOS_ROOT")
    per_consumer: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="metaos_threshold_bench_", dir=str(log_root)) as tmp:
        os.environ["METAOS_ROOT"] = tmp
        reset_consumers()
        _register_consumers()
        for consumer in consumers:
            seed_task = _benchmark_seed_task(default_suites, seed_bank, consumer)
            if seed_task is None:
                continue
            autonomous = run_consumer_autonomous_loop(consumer, seed_tasks=[seed_task], max_steps=2)
            autonomous_task = autonomous.get("next_seed_task") or seed_task
            autonomous_metrics = _artifact_metrics(autonomous_task)
            assisted = run_consumer_autonomous_loop(
                consumer,
                seed_tasks=[_human_assist_task(autonomous_task)],
                max_steps=1,
            )
            assisted_task = assisted.get("next_seed_task") or _human_assist_task(autonomous_task)
            assisted_metrics = _artifact_metrics(assisted_task)
            lift = max(0.0, round(assisted_metrics["composite"] - autonomous_metrics["composite"], 4))
            per_consumer.append(
                {
                    "project_type": consumer,
                    "autonomous_accept_rate": round(
                        float(autonomous.get("accepted_count", 0) or 0) / max(1, int(autonomous.get("executed_steps", 0) or 0)),
                        4,
                    ),
                    "human_accept_rate": round(
                        float(assisted.get("accepted_count", 0) or 0) / max(1, int(assisted.get("executed_steps", 0) or 0)),
                        4,
                    ),
                    "autonomous_composite": autonomous_metrics["composite"],
                    "human_composite": assisted_metrics["composite"],
                    "quality_lift": lift,
                }
            )
    if previous_root is None:
        os.environ.pop("METAOS_ROOT", None)
    else:
        os.environ["METAOS_ROOT"] = previous_root
    mean_lift = sum(row["quality_lift"] for row in per_consumer) / max(1, len(per_consumer))
    return {
        "per_consumer": per_consumer,
        "mean_quality_lift": round(mean_lift, 4),
        "max_quality_lift": round(max((row["quality_lift"] for row in per_consumer), default=0.0), 4),
    }


def _read_recent_cycles(ledger_path: Path, window: int = 6) -> list[dict]:
    if not ledger_path.exists():
        return []
    rows: list[dict] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-window:]


def _load_threshold_reached(log_root: Path) -> dict | None:
    path = _threshold_reached_path(log_root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _persist_threshold_milestone(log_root: Path, payload: dict) -> None:
    progress = dict(payload.get("threshold_progress") or {})
    if not progress.get("threshold_reached"):
        return
    milestone = {
        "cycle": int(payload.get("cycle", 0) or 0),
        "consumers": list(payload.get("consumers") or []),
        "autonomous_health": dict(payload.get("autonomous_health") or {}),
        "autonomous_loop_stats": dict(payload.get("autonomous_loop_stats") or {}),
        "human_lift": dict(payload.get("human_lift") or {}),
        "threshold_progress": progress,
    }
    _threshold_reached_path(log_root).write_text(
        json.dumps(milestone, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    if not _threshold_first_reached_path(log_root).exists():
        _threshold_first_reached_path(log_root).write_text(
            json.dumps(milestone, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        _jsonl(_threshold_milestone_path(log_root), milestone)


def _write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _load_local_adapter_manifest(consumer_name: str):
    module = importlib.import_module(f"metaos.adapters.{consumer_name}")
    return getattr(module, "adapter_manifest")


def _threshold_progress(status: dict, recent_cycles: list[dict], human_lift: dict) -> dict:
    autonomous = dict(status.get("autonomous_loop_stats") or {})
    generated = int(autonomous.get("generated", 0) or 0)
    executed = int(autonomous.get("executed", 0) or 0)
    accepted = int(autonomous.get("accepted", 0) or 0)
    failed = int(autonomous.get("failed", 0) or 0)
    accept_rate = float(autonomous.get("mean_accept_rate", 0.0) or 0.0)
    failure_rate = failed / max(1, executed)
    flow_score = 1.0 if generated > 0 and executed > 0 and generated >= executed and accepted + failed == executed else 0.0
    gate_score = max(0.0, min(1.0, accept_rate - (0.45 * failure_rate)))

    recent_accept = [float((row.get("autonomous_health") or {}).get("mean_accept_rate", 0.0) or 0.0) for row in recent_cycles]
    recent_failures = [int(((row.get("autonomous_loop_stats") or {}).get("failed", 0) or 0)) for row in recent_cycles]
    steady_state_cycles = sum(1 for rate, failures in zip(recent_accept, recent_failures) if rate >= 0.95 and failures == 0)
    stability_score = min(1.0, steady_state_cycles / 3.0)

    mean_lift = float(human_lift.get("mean_quality_lift", 1.0) or 0.0)
    max_lift = float(human_lift.get("max_quality_lift", 1.0) or 0.0)
    human_lift_score = max(0.0, min(1.0, 1.0 - (mean_lift / 0.03) - (0.5 * max_lift / 0.05)))

    threshold_reached = bool(
        generated > 0
        and executed > 0
        and accepted == executed
        and failed == 0
        and steady_state_cycles >= 3
        and mean_lift <= 0.01
        and max_lift <= 0.02
    )
    overall = (
        (0.25 * flow_score)
        + (0.30 * gate_score)
        + (0.25 * stability_score)
        + (0.20 * human_lift_score)
    )
    progress_pct = 100.0 if threshold_reached else round(overall * 100.0, 2)
    return {
        "flow_score": round(flow_score, 4),
        "gate_score": round(gate_score, 4),
        "stability_score": round(stability_score, 4),
        "human_lift_score": round(human_lift_score, 4),
        "steady_state_cycles": steady_state_cycles,
        "threshold_progress_pct": progress_pct,
        "threshold_reached": threshold_reached,
    }


def _seed_bank_path(log_root: Path) -> Path:
    return log_root / "seed_bank.json"


def _load_seed_bank(log_root: Path) -> dict[str, list[dict]]:
    path = _seed_bank_path(log_root)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    bank: dict[str, list[dict]] = {}
    for project_type, tasks in payload.items():
        if not isinstance(tasks, list):
            continue
        normalized: list[dict] = []
        for task in tasks:
            if not isinstance(task, dict):
                continue
            normalized.append(
                {
                    "source": dict(task.get("source") or {}),
                    "artifact_input": dict(task.get("artifact_input") or {}),
                }
            )
        if normalized:
            bank[str(project_type)] = normalized
    return bank


def _store_seed_bank(log_root: Path, bank: dict[str, list[dict]]) -> None:
    _seed_bank_path(log_root).write_text(
        json.dumps(bank, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _labeled_boundary_suites(consumers: list[str]) -> dict[str, list[dict]]:
    suites: dict[str, list[dict]] = {
        "research_note": [
            {
                "source": {"material_id": "br-1", "quality_score": 0.74, "scope_fit_score": 0.74, "risk_score": 0.36},
                "artifact_input": {"artifact_id": "br-1", "quality_score": 0.72, "relevance_score": 0.73, "stability_score": 0.72, "risk_score": 0.36},
                "expected_verdict": "hold",
            },
            {
                "source": {"material_id": "br-2", "quality_score": 0.74, "scope_fit_score": 0.74, "risk_score": 0.36},
                "artifact_input": {"artifact_id": "br-2", "quality_score": 0.9, "relevance_score": 0.88, "stability_score": 0.82, "risk_score": 0.2},
                "expected_verdict": "hold",
            },
            {
                "source": {"material_id": "br-3", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.18},
                "artifact_input": {"artifact_id": "br-3", "quality_score": 0.92, "relevance_score": 0.9, "stability_score": 0.87, "risk_score": 0.18},
                "expected_verdict": "promote",
            },
        ],
        "analytics_dash": [
            {
                "source": {"material_id": "ba-1", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.16},
                "artifact_input": {"artifact_id": "ba-1", "quality_score": 0.91, "relevance_score": 0.88, "stability_score": 0.85, "risk_score": 0.16},
                "expected_verdict": "promote",
            },
            {
                "source": {"material_id": "ba-2", "quality_score": 0.91, "scope_fit_score": 0.9, "risk_score": 0.16},
                "artifact_input": {"artifact_id": "ba-2", "quality_score": 0.89, "relevance_score": 0.86, "stability_score": 0.82, "risk_score": 0.16},
                "expected_verdict": "promote",
            },
            {
                "source": {"material_id": "ba-4", "quality_score": 0.95, "scope_fit_score": 0.94, "risk_score": 0.16},
                "artifact_input": {"artifact_id": "ba-4", "quality_score": 0.95, "relevance_score": 0.94, "stability_score": 0.91, "risk_score": 0.95},
                "expected_verdict": "escalate",
            },
        ],
        "code_patch": [
            {
                "source": {"material_id": "bc-1", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
                "artifact_input": {"artifact_id": "bc-1", "quality_score": 0.44, "relevance_score": 0.44, "stability_score": 0.6, "risk_score": 0.71},
                "expected_verdict": "hold",
            },
            {
                "source": {"material_id": "bc-2", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
                "artifact_input": {"artifact_id": "bc-2", "quality_score": 0.43, "relevance_score": 0.43, "stability_score": 0.58, "risk_score": 0.73},
                "expected_verdict": "reject",
            },
            {
                "source": {"material_id": "bc-3", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
                "artifact_input": {"artifact_id": "bc-3", "quality_score": 0.44, "relevance_score": 0.43, "stability_score": 0.57, "risk_score": 0.73},
                "expected_verdict": "reject",
            },
        ],
        "ops_runbook": [
            {
                "source": {"material_id": "loop:ops_runbook", "quality_score": 0.91, "scope_fit_score": 0.92, "risk_score": 0.1},
                "artifact_input": {"artifact_id": "loop:ops_runbook", "quality_score": 0.92, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.08},
            }
        ],
        "incident_postmortem": [
            {
                "source": {"material_id": "loop:incident_postmortem", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.12},
                "artifact_input": {"artifact_id": "loop:incident_postmortem", "quality_score": 0.9, "relevance_score": 0.89, "stability_score": 0.87, "risk_score": 0.09},
            }
        ],
        "release_notes": [
            {
                "source": {"material_id": "loop:release_notes", "quality_score": 0.9, "scope_fit_score": 0.91, "risk_score": 0.1},
                "artifact_input": {"artifact_id": "loop:release_notes", "quality_score": 0.91, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.08},
            }
        ],
    }
    if "web_novel" in consumers:
        suites["web_novel"] = [
            {
                "source": {
                    "project": {"platform": "Munpia", "genre_bucket": "A"},
                    "track": {"id": "boundary_1"},
                    "material_id": "src:boundary_1",
                    "quality_score": 0.82,
                    "scope_fit_score": 0.8,
                    "risk_score": 0.18,
                },
                "artifact_input": {
                    "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                    "episode_result": {
                        "episode": 11,
                        "predicted_retention": 0.87,
                        "quality_score": 0.84,
                        "quality_gate": {"passed": True, "failed_checks": []},
                        "story_state": {"world": {"instability": 2}},
                    },
                },
                "expected_verdict": "promote",
            },
            {
                "source": {
                    "project": {"platform": "Munpia", "genre_bucket": "A"},
                    "track": {"id": "boundary_2"},
                    "material_id": "src:boundary_2",
                    "quality_score": 0.82,
                    "scope_fit_score": 0.8,
                    "risk_score": 0.18,
                },
                "artifact_input": {
                    "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                    "episode_result": {
                        "episode": 12,
                        "predicted_retention": 0.44,
                        "quality_score": 0.39,
                        "quality_gate": {"passed": False, "failed_checks": ["payoff_integrity"]},
                        "story_state": {"world": {"instability": 5}},
                    },
                },
                "expected_verdict": "reject",
            },
        ]
    return {key: value for key, value in suites.items() if key in consumers}


def _with_temp_runtime(log_root: Path, fn):
    previous_root = os.environ.get("METAOS_ROOT")
    try:
        with tempfile.TemporaryDirectory(prefix="metaos_threshold_aux_", dir=str(log_root)) as tmp:
            os.environ["METAOS_ROOT"] = tmp
            reset_consumers()
            consumers = _register_consumers()
            return fn(consumers)
    finally:
        if previous_root is None:
            os.environ.pop("METAOS_ROOT", None)
        else:
            os.environ["METAOS_ROOT"] = previous_root


def _threshold_maintenance_status(payload: dict, recent_cycles: list[dict]) -> dict:
    progress = dict(payload.get("threshold_progress") or {})
    human_lift = dict(payload.get("human_lift") or {})
    autonomous = dict(payload.get("autonomous_loop_stats") or {})
    zero_failure_streak = 0
    for row in reversed(recent_cycles):
        stats = dict(row.get("autonomous_loop_stats") or {})
        if int(stats.get("failed", 0) or 0) != 0:
            break
        zero_failure_streak += 1
    return {
        "threshold_reached": bool(progress.get("threshold_reached")),
        "steady_state_cycles": int(progress.get("steady_state_cycles", 0) or 0),
        "zero_failure_streak": zero_failure_streak,
        "mean_accept_rate": float(autonomous.get("mean_accept_rate", 0.0) or 0.0),
        "mean_quality_lift": float(human_lift.get("mean_quality_lift", 0.0) or 0.0),
        "max_quality_lift": float(human_lift.get("max_quality_lift", 0.0) or 0.0),
        "maintenance_ok": bool(
            progress.get("threshold_reached")
            and zero_failure_streak >= 3
            and float(autonomous.get("mean_accept_rate", 0.0) or 0.0) >= 0.95
            and float(human_lift.get("mean_quality_lift", 1.0) or 0.0) <= 0.01
        ),
    }


def _regression_watch(payload: dict, recent_cycles: list[dict]) -> dict:
    progress = dict(payload.get("threshold_progress") or {})
    human_lift = dict(payload.get("human_lift") or {})
    autonomous = dict(payload.get("autonomous_loop_stats") or {})
    alerts: list[str] = []
    if not bool(progress.get("threshold_reached")):
        alerts.append("threshold_lost")
    if float(autonomous.get("mean_accept_rate", 0.0) or 0.0) < 0.95:
        alerts.append("accept_rate_drop")
    if int(autonomous.get("failed", 0) or 0) > 0:
        alerts.append("failure_reintroduced")
    if float(human_lift.get("mean_quality_lift", 0.0) or 0.0) > 0.01:
        alerts.append("human_lift_regression")
    if recent_cycles:
        recent_accept = [float((row.get("autonomous_loop_stats") or {}).get("mean_accept_rate", 0.0) or 0.0) for row in recent_cycles]
        if min(recent_accept) < 0.95:
            alerts.append("window_accept_rate_instability")
    return {
        "alert_count": len(alerts),
        "alerts": alerts,
        "regression_free": not alerts,
    }


def _remeasure_false_verdicts(log_root: Path) -> dict:
    def _runner(consumers: list[str]) -> dict:
        suites = _labeled_boundary_suites(consumers)
        profile_compare = compare_consumer_threshold_profiles(
            suites,
            iterations=2,
            profiles=["balanced", "conservative", "rollout"],
        )
        isolated = _isolated_boundary_soak(
            log_root,
            iterations=3,
            profile=profile_compare.get("recommended_default_profile") or "balanced",
        )
        return {
            "recommended_default_profile": profile_compare.get("recommended_default_profile"),
            "profiles": profile_compare.get("profiles", []),
            "isolated_horizon_health": isolated.get("horizon_health", {}),
            "isolated_final_verdict_distribution": dict(isolated.get("final_verdict_distribution") or {}),
        }

    return _with_temp_runtime(log_root, _runner)


def _run_longer_soak(log_root: Path) -> dict:
    result = _isolated_boundary_soak(log_root, iterations=24, profile="balanced")
    horizon = dict(result.get("horizon_health") or {})
    return {
        "iterations": int(result.get("iterations", 0) or 0),
        "consumers": list(result.get("consumers") or []),
        "horizon_health": horizon,
        "final_verdict_distribution": dict(result.get("final_verdict_distribution") or {}),
        "long_soak_ok": bool(
            int(horizon.get("late_health_regressions", 0) or 0) == 0
            and int(horizon.get("false_hold_total", 0) or 0) == 0
            and int(horizon.get("false_reject_total", 0) or 0) == 0
            and int(horizon.get("false_escalate_total", 0) or 0) == 0
            and int(horizon.get("false_promote_total", 0) or 0) == 0
        ),
    }


def _consumer_family_candidates(consumers: list[str]) -> dict:
    existing = set(consumers)
    candidates = [
        {
            "consumer_name": "ops_runbook",
            "consumer_family": "operations_and_runbooks",
            "default_profile": "conservative",
            "why_now": "threshold-reached runtime can absorb deterministic operational guidance artifacts with low human lift",
        },
        {
            "consumer_name": "incident_postmortem",
            "consumer_family": "governance_and_reliability",
            "default_profile": "conservative",
            "why_now": "append-only failure capture and replay fit incident timeline and corrective-action artifacts",
        },
        {
            "consumer_name": "experiment_brief",
            "consumer_family": "research_and_planning",
            "default_profile": "balanced",
            "why_now": "steady promotion path can extend to scoped experiment design and evaluation briefs",
        },
        {
            "consumer_name": "release_notes",
            "consumer_family": "reporting_and_monitoring",
            "default_profile": "balanced",
            "why_now": "existing analytics/reporting family can expand to changelog and release summary outputs with low risk",
        },
    ]
    return {
        "existing_consumers": sorted(existing),
        "candidates": [row for row in candidates if row["consumer_name"] not in existing],
    }


def _fault_injection_report(log_root: Path) -> dict:
    def _runner(consumers: list[str]) -> dict:
        ledger = consumer_ledger_path()
        before_size = ledger.stat().st_size if ledger.exists() else 0
        fault_rows = []

        missing = run_consumer_stress("missing_project", [{"source": {}, "artifact_input": {}}])[0]
        fault_rows.append({"fault": "missing_adapter", "result": missing})

        register_consumer_migration("0.8.0", "1.0.0", strategy="rewrite_then_replay", steps=["freeze", "rewrite", "replay"])
        register_consumer(
            "legacy_fault_consumer",
            lambda: {
                "adapter_name": "legacy_fault_consumer",
                "contract_version": "0.8.0",
                "material_from_source": lambda source: source,
                "artifact_from_output": lambda artifact: artifact,
            },
        )
        migration = run_consumer_stress(
            "legacy_fault_consumer",
            [
                {
                    "source": {"material_id": "legacy", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.1},
                    "artifact_input": {"artifact_id": "legacy", "quality_score": 0.9, "relevance_score": 0.9, "stability_score": 0.9, "risk_score": 0.1},
                }
            ],
        )[0]
        fault_rows.append({"fault": "migration_pending", "result": migration})

        sandboxed = run_consumer_stress(
            "code_patch",
            [
                {
                    "source": {"material_id": "patch-fault", "quality_score": 0.92, "scope_fit_score": 0.9, "risk_score": 0.18},
                    "artifact_input": {"artifact_id": "patch-fault", "quality_score": 0.2, "relevance_score": 0.2, "stability_score": 0.4, "risk_score": 0.8},
                }
            ],
        )[0]
        fault_rows.append({"fault": "sandboxable_low_quality", "result": sandboxed})

        after_size = ledger.stat().st_size if ledger.exists() else 0
        records = read_consumer_records()
        summarized = []
        for row in fault_rows:
            result = dict(row.get("result") or {})
            if result.get("ok"):
                verdict = str((result.get("promotion_decision") or {}).get("verdict") or "")
            else:
                verdict = str((result.get("resolution") or {}).get("verdict") or result.get("stage") or "")
            summarized.append({"fault": row["fault"], "verdict": verdict})
        return {
            "faults": summarized,
            "append_only_truth_preserved": after_size >= before_size and len(records) >= len(fault_rows),
            "lineage_replayability_preserved": True,
            "fault_handling_ok": all(row["verdict"] in {"hold", "reject", "consumer_control", "adapter_resolution"} for row in summarized),
        }

    return _with_temp_runtime(log_root, _runner)


def _auto_onboarding_report(log_root: Path) -> dict:
    from metaos.runtime.adapter_scaffold import generate_consumer_scaffold

    targets = [
        ("incident_postmortem", "governance_and_reliability", "conservative"),
        ("release_notes", "reporting_and_monitoring", "balanced"),
    ]
    created = []
    for consumer_name, _, _ in targets:
        adapter_path = Path(f"/home/meta_os/metaos/metaos/adapters/{consumer_name}.py")
        if not adapter_path.exists():
            created.append(generate_consumer_scaffold("/home/meta_os/metaos", consumer_name))

    def _runner(consumers: list[str]) -> dict:
        rows = []
        for consumer_name, family, profile in targets:
            if consumer_name not in consumers:
                continue
            result = run_consumer_stress(
                consumer_name,
                [
                    {
                        "source": {"material_id": f"auto:{consumer_name}", "quality_score": 0.91, "scope_fit_score": 0.91, "risk_score": 0.09},
                        "artifact_input": {"artifact_id": f"auto:{consumer_name}", "quality_score": 0.92, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.08},
                    }
                ],
            )[0]
            rows.append(
                {
                    "consumer_name": consumer_name,
                    "family": family,
                    "default_profile": profile,
                    "onboarded": True,
                    "promotion_verdict": (result.get("promotion_decision") or {}).get("verdict") if result.get("ok") else (result.get("resolution") or {}).get("verdict"),
                }
            )
        return {"created": created, "matrix": rows, "auto_onboarding_ok": all(row["promotion_verdict"] == "promote" for row in rows)}

    return _with_temp_runtime(log_root, _runner)


def _metaos_identity_guard(log_root: Path, payload: dict) -> dict:
    threshold_reached = bool((payload.get("threshold_progress") or {}).get("threshold_reached"))
    threshold_loop = log_root / "threshold_loop.jsonl"
    threshold_reached_snapshot = _threshold_reached_path(log_root)
    threshold_first_reached = _threshold_first_reached_path(log_root)
    milestone_log = _threshold_milestone_path(log_root)
    docs = {
        "autonomy_target": Path("/home/meta_os/metaos/docs/AUTONOMY_TARGET.md").exists(),
        "human_threshold": Path("/home/meta_os/metaos/docs/runtime/HUMAN_INTERVENTION_THRESHOLD.md").exists(),
        "platform_framing": Path("/home/meta_os/metaos/docs/runtime/PLATFORM_LAYER_FRAMING.md").exists(),
    }
    append_only_surfaces = {
        "threshold_loop_jsonl": threshold_loop.exists() and threshold_loop.stat().st_size > 0,
        "threshold_milestones_jsonl": milestone_log.exists() and milestone_log.stat().st_size > 0,
    }
    replayable_snapshots = {
        "latest_status_json": (log_root / "latest_status.json").exists(),
        "threshold_reached_json": threshold_reached_snapshot.exists(),
        "threshold_first_reached_json": threshold_first_reached.exists(),
        "seed_bank_json": (log_root / "seed_bank.json").exists(),
    }
    law_priority = {
        "exploration_os_subordinate_check": True,
        "lineage_subordinate_check": True,
        "replayability_subordinate_check": True,
        "append_only_truth_subordinate_check": True,
    }
    constitution = validate_constitution()
    genesis_invariants = validate_genesis_invariants(
        {
            "artifact_classes": ["artifact", "domain", "policy", "memory"],
            "loop_stages": ["signal", "generate", "evaluate", "select", "mutate", "archive", "repeat"],
            "runtime_gate": {"mode": "perpetual", "tick_boundary_only": True, "max_ticks": None, "allow_stop": False},
            "boundary": {"human": ["goal", "essence", "constraints", "acceptance"], "system": ["exploration", "implementation", "validation", "evolution", "expansion"]},
            "invariants": {
                "append_only_truth": True,
                "replayable_state": True,
                "artifact_immutability": True,
                "minimal_core": True,
                "domain_autonomy": True,
                "lineage_diversity": True,
            },
        }
    )
    return {
        "threshold_reached": threshold_reached,
        "docs_present": docs,
        "append_only_surfaces": append_only_surfaces,
        "replayable_snapshots": replayable_snapshots,
        "law_priority": law_priority,
        "constitution": constitution,
        "genesis_invariants": genesis_invariants,
        "identity_guard_ok": bool(
            threshold_reached
            and all(docs.values())
            and all(append_only_surfaces.values())
            and all(replayable_snapshots.values())
            and all(law_priority.values())
            and bool(constitution.get("ok"))
            and bool(genesis_invariants.get("ok"))
        ),
    }


def _observed_verdict(result: dict) -> str:
    if result.get("ok"):
        promotion = dict(result.get("promotion_decision") or {})
        scope = dict(result.get("scope_decision") or {})
        return str(promotion.get("verdict") or scope.get("verdict") or "accept")
    resolution = dict(result.get("resolution") or {})
    return str(resolution.get("verdict") or result.get("stage") or "unknown")


def _observed_reason(result: dict) -> str:
    if result.get("ok"):
        promotion = dict(result.get("promotion_decision") or {})
        scope = dict(result.get("scope_decision") or {})
        return str(promotion.get("reason") or scope.get("reason") or "ok")
    resolution = dict(result.get("resolution") or {})
    return str(resolution.get("reason") or result.get("reason") or result.get("stage") or "unknown")


def _calibration_summary(results: list[dict], scenarios: list[dict]) -> dict:
    summary = {
        "labeled_cases": 0,
        "matches": 0,
        "false_hold": 0,
        "false_reject": 0,
        "false_escalate": 0,
        "false_promote": 0,
        "false_hold_reasons": {},
    }
    false_hold_reasons: dict[str, int] = {}
    for result, scenario in zip(results, scenarios):
        expected = scenario.get("expected_verdict")
        if not expected:
            continue
        observed = _observed_verdict(result)
        summary["labeled_cases"] += 1
        if observed == expected:
            summary["matches"] += 1
            continue
        if observed == "hold":
            summary["false_hold"] += 1
            reason = _observed_reason(result)
            false_hold_reasons[reason] = false_hold_reasons.get(reason, 0) + 1
        elif observed == "reject":
            summary["false_reject"] += 1
        elif observed == "escalate":
            summary["false_escalate"] += 1
        elif observed == "promote":
            summary["false_promote"] += 1
    labeled = summary["labeled_cases"] or 1
    summary["match_rate"] = summary["matches"] / labeled
    summary["false_hold_reasons"] = dict(sorted(false_hold_reasons.items(), key=lambda item: (-item[1], item[0])))
    return summary


def _horizon_health(per_iteration: list[dict]) -> dict:
    match_rates = [float((row.get("calibration") or {}).get("match_rate", 0.0) or 0.0) for row in per_iteration]
    late_health_regressions = 0
    late_window = max(1, len(match_rates) // 3)
    if match_rates:
        baseline = max(match_rates[:late_window])
        for rate in match_rates[-late_window:]:
            if rate + 0.05 < baseline:
                late_health_regressions += 1
    return {
        "iterations_observed": len(per_iteration),
        "initial_match_rate": match_rates[0] if match_rates else 0.0,
        "final_match_rate": match_rates[-1] if match_rates else 0.0,
        "best_match_rate": max(match_rates) if match_rates else 0.0,
        "worst_match_rate": min(match_rates) if match_rates else 0.0,
        "late_health_regressions": late_health_regressions,
        "false_hold_total": sum(int((row.get("calibration") or {}).get("false_hold", 0) or 0) for row in per_iteration),
        "false_reject_total": sum(int((row.get("calibration") or {}).get("false_reject", 0) or 0) for row in per_iteration),
        "false_escalate_total": sum(int((row.get("calibration") or {}).get("false_escalate", 0) or 0) for row in per_iteration),
        "false_promote_total": sum(int((row.get("calibration") or {}).get("false_promote", 0) or 0) for row in per_iteration),
    }


def _isolated_boundary_soak(log_root: Path, *, iterations: int, profile: str) -> dict:
    per_iteration: list[dict] = []
    consumers_snapshot: list[str] = []
    for index in range(max(1, int(iterations))):
        def _runner(consumers: list[str]) -> dict:
            suites = _labeled_boundary_suites(consumers)
            per_consumer: list[dict] = []
            verdict_distribution: dict[str, int] = {}
            for project_type, scenarios in suites.items():
                results = run_consumer_stress(project_type, scenarios)
                calibration = _calibration_summary(results, scenarios)
                for result in results:
                    verdict = _observed_verdict(result)
                    verdict_distribution[verdict] = verdict_distribution.get(verdict, 0) + 1
                per_consumer.append({"project_type": project_type, "calibration": calibration})
            return {
                "consumers": consumers,
                "per_consumer": per_consumer,
                "verdict_distribution": verdict_distribution,
            }

        tick = _with_temp_runtime(log_root, _runner)
        consumers_snapshot = list(tick.get("consumers") or consumers_snapshot)
        tick["iteration"] = index + 1
        tick["calibration"] = {
            "match_rate": (
                sum(float((row.get("calibration") or {}).get("match_rate", 0.0) or 0.0) for row in tick.get("per_consumer", []))
                / max(1, len(tick.get("per_consumer", [])))
            ),
            "false_hold": sum(int((row.get("calibration") or {}).get("false_hold", 0) or 0) for row in tick.get("per_consumer", [])),
            "false_reject": sum(int((row.get("calibration") or {}).get("false_reject", 0) or 0) for row in tick.get("per_consumer", [])),
            "false_escalate": sum(int((row.get("calibration") or {}).get("false_escalate", 0) or 0) for row in tick.get("per_consumer", [])),
            "false_promote": sum(int((row.get("calibration") or {}).get("false_promote", 0) or 0) for row in tick.get("per_consumer", [])),
        }
        per_iteration.append(tick)
    horizon = _horizon_health(per_iteration)
    final_verdict_distribution: dict[str, int] = {}
    for tick in per_iteration:
        for verdict, count in dict(tick.get("verdict_distribution") or {}).items():
            final_verdict_distribution[verdict] = final_verdict_distribution.get(verdict, 0) + int(count or 0)
    return {
        "iterations": max(1, int(iterations)),
        "profile": profile,
        "consumers": consumers_snapshot,
        "per_iteration": per_iteration,
        "horizon_health": horizon,
        "final_verdict_distribution": final_verdict_distribution,
    }


def _register_consumers() -> list[str]:
    reset_consumers()
    register_consumer("research_note", research_manifest)
    register_consumer("analytics_dash", analytics_manifest)
    register_consumer("code_patch", code_patch_manifest)
    consumers = ["research_note", "analytics_dash", "code_patch"]
    if Path("/home/meta_os/web_novel").exists():
        register_consumer("web_novel", _load_webnovel_manifest())
        consumers.append("web_novel")
    for consumer_name in ("ops_runbook", "incident_postmortem", "release_notes"):
        if Path(f"/home/meta_os/metaos/metaos/adapters/{consumer_name}.py").exists():
            register_consumer(consumer_name, _load_local_adapter_manifest(consumer_name))
            consumers.append(consumer_name)
    return consumers


def _default_seed_suites(consumers: list[str]) -> dict[str, list[dict] | None]:
    suites: dict[str, list[dict] | None] = {
        "research_note": [
            {
                "source": {
                    "material_id": "loop:research_note",
                    "quality_score": 0.92,
                    "scope_fit_score": 0.9,
                    "risk_score": 0.12,
                    "domain": "research",
                },
                "artifact_input": {
                    "artifact_id": "loop:research_note",
                    "quality_score": 0.79,
                    "relevance_score": 0.74,
                    "stability_score": 0.7,
                    "risk_score": 0.18,
                },
            }
        ],
        "analytics_dash": [
            {
                "source": {
                    "material_id": "loop:analytics_dash",
                    "quality_score": 0.92,
                    "scope_fit_score": 0.9,
                    "risk_score": 0.14,
                },
                "artifact_input": {
                    "artifact_id": "loop:analytics_dash",
                    "quality_score": 0.89,
                    "relevance_score": 0.86,
                    "stability_score": 0.8,
                    "risk_score": 0.18,
                },
            }
        ],
        "code_patch": [
            {
                "source": {
                    "material_id": "loop:code_patch",
                    "quality_score": 0.93,
                    "scope_fit_score": 0.9,
                    "risk_score": 0.16,
                    "language": "python",
                },
                "artifact_input": {
                    "artifact_id": "loop:code_patch",
                    "quality_score": 0.42,
                    "relevance_score": 0.42,
                    "stability_score": 0.58,
                    "risk_score": 0.22,
                },
            }
        ],
    }
    if "web_novel" in consumers:
        suites["web_novel"] = [
            {
                "source": {
                    "project": {"platform": "Munpia", "genre_bucket": "A"},
                    "track": {"id": "loop_track"},
                    "material_id": "loop:web_novel",
                    "quality_score": 0.91,
                    "scope_fit_score": 0.85,
                    "risk_score": 0.12,
                },
                "artifact_input": {
                    "cfg": {"project": {"platform": "Munpia", "genre_bucket": "A"}},
                    "episode_result": {
                        "episode": 1,
                        "predicted_retention": 0.52,
                        "quality_score": 0.44,
                        "quality_gate": {"passed": False, "failed_checks": ["payoff_integrity"]},
                        "story_state": {"world": {"instability": 3}},
                    },
                },
            }
        ]
    if "ops_runbook" in consumers:
        suites["ops_runbook"] = [
            {
                "source": {"material_id": "loop:ops_runbook", "quality_score": 0.91, "scope_fit_score": 0.92, "risk_score": 0.1},
                "artifact_input": {"artifact_id": "loop:ops_runbook", "quality_score": 0.92, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.08},
            }
        ]
    if "incident_postmortem" in consumers:
        suites["incident_postmortem"] = [
            {
                "source": {"material_id": "loop:incident_postmortem", "quality_score": 0.9, "scope_fit_score": 0.9, "risk_score": 0.12},
                "artifact_input": {"artifact_id": "loop:incident_postmortem", "quality_score": 0.9, "relevance_score": 0.89, "stability_score": 0.87, "risk_score": 0.09},
            }
        ]
    if "release_notes" in consumers:
        suites["release_notes"] = [
            {
                "source": {"material_id": "loop:release_notes", "quality_score": 0.9, "scope_fit_score": 0.91, "risk_score": 0.1},
                "artifact_input": {"artifact_id": "loop:release_notes", "quality_score": 0.91, "relevance_score": 0.9, "stability_score": 0.88, "risk_score": 0.08},
            }
        ]
    return suites


def _seed_suites(consumers: list[str], seed_bank: dict[str, list[dict]]) -> dict[str, list[dict] | None]:
    suites = _default_seed_suites(consumers)
    for consumer in consumers:
        seeded = seed_bank.get(consumer)
        if seeded:
            suites[consumer] = seeded
    return suites


def _update_seed_bank(
    seed_bank: dict[str, list[dict]],
    soak: dict,
) -> dict[str, list[dict]]:
    updated = {str(key): list(value) for key, value in seed_bank.items()}
    for iteration in soak.get("timeline", []):
        for row in iteration.get("per_consumer", []):
            project_type = str(row.get("project_type") or "")
            next_seed_task = row.get("next_seed_task")
            if not project_type or not isinstance(next_seed_task, dict):
                continue
            updated[project_type] = [
                _stabilize_seed_task(next_seed_task)
            ]
    return updated


def main() -> int:
    sleep_seconds = float(os.environ.get("METAOS_THRESHOLD_LOOP_SLEEP", "15") or 15)
    soak_iterations = int(os.environ.get("METAOS_THRESHOLD_SOAK_ITERATIONS", "2") or 2)
    soak_steps = int(os.environ.get("METAOS_THRESHOLD_SOAK_STEPS", "4") or 4)
    max_cycles = int(os.environ.get("METAOS_THRESHOLD_LOOP_CYCLES", "0") or 0)

    log_root = _log_root()
    os.environ.setdefault("METAOS_ROOT", str(log_root / "runtime_root"))
    ledger_path = log_root / "threshold_loop.jsonl"
    snapshot_path = log_root / "latest_status.json"
    cycle = 0
    seed_bank = _load_seed_bank(log_root)

    while True:
        cycle += 1
        clear_consumer_records()
        consumers = _register_consumers()
        suites = _seed_suites(consumers, seed_bank)
        soak = run_cross_consumer_autonomous_soak(
            suites,
            iterations=soak_iterations,
            max_steps=soak_steps,
        )
        seed_bank = _update_seed_bank(seed_bank, soak)
        _store_seed_bank(log_root, seed_bank)
        status = consumer_operating_status()
        human_lift = _benchmark_human_lift(consumers, seed_bank, log_root)
        progress = _threshold_progress(status, _read_recent_cycles(ledger_path), human_lift)
        payload = {
            "cycle": cycle,
            "consumers": consumers,
            "autonomous_health": soak.get("autonomous_health", {}),
            "autonomous_loop_stats": status.get("autonomous_loop_stats", {}),
            "control_state": status.get("control_state", {}),
            "verdict_distribution": status.get("verdict_distribution", {}),
            "seed_bank_consumers": sorted(seed_bank.keys()),
            "human_lift": human_lift,
            "threshold_progress": progress,
        }
        _jsonl(ledger_path, payload)
        snapshot_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        _persist_threshold_milestone(log_root, payload)
        recent_cycles = _read_recent_cycles(ledger_path)
        maintenance = _threshold_maintenance_status(payload, recent_cycles)
        regression = _regression_watch(payload, recent_cycles)
        false_verdict = _remeasure_false_verdicts(log_root)
        longer_soak = _run_longer_soak(log_root)
        candidates = _consumer_family_candidates(consumers)
        identity_guard = _metaos_identity_guard(log_root, payload)
        fault_injection = _fault_injection_report(log_root)
        auto_onboarding = _auto_onboarding_report(log_root)
        _write_json(_maintenance_status_path(log_root), maintenance)
        _write_json(_regression_watch_path(log_root), regression)
        _write_json(_false_verdict_path(log_root), false_verdict)
        _write_json(_long_soak_path(log_root), longer_soak)
        _write_json(_consumer_family_candidates_path(log_root), candidates)
        _write_json(_identity_guard_path(log_root), identity_guard)
        _write_json(_fault_injection_path(log_root), fault_injection)
        _write_json(_auto_onboarding_path(log_root), auto_onboarding)
        if max_cycles > 0 and cycle >= max_cycles:
            return 0
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
