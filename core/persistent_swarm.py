import importlib
import json
import multiprocessing as mp
import os
import random
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None

STRATEGY_KEYS = ("quality", "novelty", "diversity", "efficiency", "cost")
ARTIFACT_DIR = Path("artifact_store")
STATE_DIR = Path("state")
CHECKPOINT_PATH = STATE_DIR / "checkpoint.json"
METRICS_PATH = Path("metrics.jsonl")
EVENTS_PATH = Path("events.jsonl")

POPULATION_SIZE = 64
MIN_WORKERS = 1
MAX_WORKERS = max(MIN_WORKERS, mp.cpu_count() * 4)
ARTIFACT_LIMIT = 5000
ARTIFACT_PURGE_COUNT = 2000
MUTATION_RANGE = 0.08
TICK_SLEEP_SECONDS = 1.0
POOL_TASKS_PER_CHILD = 200

DEFAULT_LLM_HOOK = os.getenv("METAOS_LLM_HOOK", "").strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def random_strategy() -> dict[str, float]:
    return {k: random.random() for k in STRATEGY_KEYS}


def normalize_strategy(strategy: Any) -> dict[str, float] | None:
    if not isinstance(strategy, dict):
        return None
    normalized: dict[str, float] = {}
    for key in STRATEGY_KEYS:
        raw = strategy.get(key)
        if raw is None:
            return None
        try:
            normalized[key] = clamp01(float(raw))
        except Exception:
            return None
    return normalized


def mutate(strategy: dict[str, float]) -> dict[str, float]:
    return {
        key: clamp01(value + random.uniform(-MUTATION_RANGE, MUTATION_RANGE))
        for key, value in strategy.items()
    }


def evaluate(strategy: dict[str, float]) -> float:
    return (
        strategy["quality"] * 0.3
        + strategy["novelty"] * 0.25
        + strategy["diversity"] * 0.2
        + strategy["efficiency"] * 0.15
        - strategy["cost"] * 0.1
    )


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        # Avoid crashing the engine for transient file issues.
        pass


def log_event(event_type: str, payload: dict[str, Any]) -> None:
    append_jsonl(
        EVENTS_PATH,
        {"timestamp": now_iso(), "event_type": event_type, "payload": payload},
    )


def log_metrics(payload: dict[str, Any]) -> None:
    append_jsonl(
        METRICS_PATH,
        {"timestamp": now_iso(), "event_type": "metrics", "payload": payload},
    )


def list_domain_modules(domains_dir: Path = Path("domains")) -> list[str]:
    modules: list[str] = []
    if not domains_dir.exists():
        return modules
    for entry in domains_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix != ".py":
            continue
        if entry.stem.startswith("_") or entry.stem == "__init__":
            continue
        modules.append(f"domains.{entry.stem}")
    return sorted(modules)


def resolve_llm_hook(llm_hook: str) -> str | None:
    hook = llm_hook.strip()
    if not hook:
        return None
    if ":" in hook:
        module_name, function_name = hook.split(":", 1)
        if module_name and function_name:
            return f"{module_name}:{function_name}"
        return None
    return f"{hook}:generate_strategy"


def call_llm_hook(resolved_hook: str | None) -> dict[str, float] | None:
    if not resolved_hook:
        return None
    module_name, function_name = resolved_hook.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        generator = getattr(module, function_name, None)
        if not callable(generator):
            return None
        return normalize_strategy(generator())
    except Exception:
        return None


def call_domain_generator(module_name: str) -> dict[str, float] | None:
    try:
        module = importlib.import_module(module_name)
        generator = getattr(module, "generate", None)
        if not callable(generator):
            return None
        return normalize_strategy(generator())
    except Exception:
        return None


def create_artifact(strategy: dict[str, float], score: float, source: str, tick: int) -> str | None:
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        artifact_id = str(uuid.uuid4())
        target_dir = ARTIFACT_DIR / artifact_id
        target_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": now_iso(),
            "strategy": strategy,
            "score": score,
            "source": source,
            "tick": tick,
        }
        with (target_dir / "artifact.json").open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True)
        return artifact_id
    except Exception as exc:
        log_event("artifact_error", {"error": str(exc)})
        return None


def cleanup_artifacts() -> int:
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        dirs = [p for p in ARTIFACT_DIR.iterdir() if p.is_dir()]
        if len(dirs) <= ARTIFACT_LIMIT:
            return 0
        dirs.sort(key=lambda p: p.stat().st_mtime)
        remove_count = min(ARTIFACT_PURGE_COUNT, len(dirs))
        for path in dirs[:remove_count]:
            shutil.rmtree(path, ignore_errors=True)
        return remove_count
    except Exception as exc:
        log_event("cleanup_error", {"error": str(exc)})
        return 0


def load_checkpoint() -> dict[str, Any]:
    default_state = {"population": [], "best_score": float("-inf"), "last_tick": 0}
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        if not CHECKPOINT_PATH.exists():
            return default_state
        with CHECKPOINT_PATH.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        population = []
        for item in raw.get("population", []):
            normalized = normalize_strategy(item)
            if normalized is not None:
                population.append(normalized)
        best_score = raw.get("best_score", float("-inf"))
        try:
            best_score = float(best_score)
        except Exception:
            best_score = float("-inf")
        last_tick = raw.get("last_tick", 0)
        try:
            last_tick = int(last_tick)
        except Exception:
            last_tick = 0
        return {"population": population, "best_score": best_score, "last_tick": last_tick}
    except Exception as exc:
        log_event("checkpoint_load_error", {"error": str(exc)})
        return default_state


def save_checkpoint(population: list[dict[str, float]], best_score: float, tick: int) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"population": population, "best_score": best_score, "last_tick": tick}
        temp_path = CHECKPOINT_PATH.with_suffix(".json.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True)
        os.replace(temp_path, CHECKPOINT_PATH)
    except Exception as exc:
        log_event("checkpoint_save_error", {"error": str(exc)})


def cpu_percent() -> float:
    if psutil is not None:
        try:
            return float(psutil.cpu_percent(interval=0.0))
        except Exception:
            pass
    try:
        load1, _, _ = os.getloadavg()
        return clamp01(load1 / max(1, mp.cpu_count())) * 100.0
    except Exception:
        return 50.0


def scaled_workers(current: int, cpu_usage: float) -> int:
    workers = current
    if cpu_usage > 80.0:
        workers = max(MIN_WORKERS, current - 1)
    elif cpu_usage < 50.0:
        workers = min(MAX_WORKERS, current + 1)
    return workers


def seed_population(population: list[dict[str, float]], target_size: int = POPULATION_SIZE) -> list[dict[str, float]]:
    seeded = list(population)
    while len(seeded) < target_size:
        seeded.append(random_strategy())
    return seeded[:target_size]


def evolve_population(results: list[dict[str, Any]], target_size: int = POPULATION_SIZE) -> list[dict[str, float]]:
    if not results:
        return seed_population([])
    ordered = sorted(results, key=lambda item: item["score"], reverse=True)
    elite_count = max(4, target_size // 4)
    elites = [item["strategy"] for item in ordered[:elite_count]]
    next_population = list(elites)
    while len(next_population) < target_size:
        base = random.choice(elites)
        next_population.append(mutate(base))
    return next_population[:target_size]


def worker(task: tuple[dict[str, float], list[str], str | None]) -> dict[str, Any]:
    base_strategy, domain_modules, llm_hook = task
    source = "random"
    generated = call_llm_hook(llm_hook)
    if generated is not None:
        source = "llm"
    else:
        if domain_modules:
            module_name = random.choice(domain_modules)
            generated = call_domain_generator(module_name)
            if generated is not None:
                source = module_name
        if generated is None:
            generated = random_strategy()
            source = "random"
    blended = {
        key: clamp01((generated[key] * 0.6) + (base_strategy[key] * 0.4))
        for key in STRATEGY_KEYS
    }
    candidate = mutate(blended)
    score = evaluate(candidate)
    return {"strategy": candidate, "score": score, "source": source}


def create_pool(worker_count: int) -> mp.pool.Pool:
    return mp.Pool(processes=worker_count, maxtasksperchild=POOL_TASKS_PER_CHILD)


def run() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    domain_modules = list_domain_modules()
    llm_hook = resolve_llm_hook(DEFAULT_LLM_HOOK)
    checkpoint = load_checkpoint()
    population = seed_population(checkpoint.get("population", []))
    best_score = float(checkpoint.get("best_score", float("-inf")))
    tick = int(checkpoint.get("last_tick", 0))

    worker_count = max(MIN_WORKERS, min(MAX_WORKERS, mp.cpu_count()))
    pool = create_pool(worker_count)

    log_event(
        "persistent_swarm_start",
        {
            "workers": worker_count,
            "domains": domain_modules,
            "llm_hook": llm_hook or "",
            "last_tick": tick,
        },
    )

    try:
        while True:
            tick += 1
            tasks = [
                (random.choice(population), domain_modules, llm_hook)
                for _ in range(worker_count)
            ]

            try:
                results = pool.map(worker, tasks)
            except Exception as exc:
                log_event("worker_batch_error", {"tick": tick, "error": str(exc)})
                results = []

            if not results:
                fallback = random_strategy()
                results = [{"strategy": fallback, "score": evaluate(fallback), "source": "recovery"}]

            for item in results:
                strategy = item["strategy"]
                score = float(item["score"])
                source = str(item["source"])
                artifact_id = create_artifact(strategy, score, source, tick)
                metric_payload = dict(strategy)
                metric_payload["score"] = score
                metric_payload["tick"] = tick
                metric_payload["source"] = source
                log_metrics(metric_payload)
                log_event(
                    "strategy_evaluated",
                    {"tick": tick, "score": score, "source": source, "artifact_id": artifact_id or ""},
                )

            batch_best = max(item["score"] for item in results)
            if batch_best > best_score:
                best_score = batch_best
                log_event("new_best_score", {"tick": tick, "best_score": best_score})

            population = evolve_population(results)
            save_checkpoint(population, best_score, tick)

            removed = cleanup_artifacts()
            if removed:
                log_event("artifacts_cleaned", {"tick": tick, "removed": removed})

            usage = cpu_percent()
            next_workers = scaled_workers(worker_count, usage)
            if next_workers != worker_count:
                old_count = worker_count
                pool.close()
                pool.join()
                worker_count = next_workers
                pool = create_pool(worker_count)
                log_event(
                    "workers_scaled",
                    {"tick": tick, "cpu_percent": usage, "from": old_count, "to": worker_count},
                )

            print(
                f"tick={tick} workers={worker_count} cpu={usage:.1f}% "
                f"batch_best={batch_best:.4f} global_best={best_score:.4f}"
            )
            time.sleep(TICK_SLEEP_SECONDS)
    except KeyboardInterrupt:
        log_event("persistent_swarm_stop", {"reason": "keyboard_interrupt", "tick": tick})
    except Exception as exc:
        log_event("persistent_swarm_crash", {"tick": tick, "error": str(exc)})
        raise
    finally:
        try:
            pool.terminate()
            pool.join()
        except Exception:
            pass


if __name__ == "__main__":
    run()
