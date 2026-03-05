import multiprocessing as mp
import os, json, uuid, random, time
from datetime import datetime, timezone

ARTIFACT_DIR = "artifact_store"


def now():
    return datetime.now(timezone.utc).isoformat()


def log_event(event_type, payload):
    with open("events.jsonl", "a") as f:
        f.write(json.dumps({
            "timestamp": now(),
            "event_type": event_type,
            "payload": payload
        }) + "\n")


def write_metrics(metrics):
    with open("metrics.jsonl", "a") as f:
        f.write(json.dumps({
            "timestamp": now(),
            "event_type": "metrics",
            "payload": metrics
        }) + "\n")


def random_strategy():
    return {
        "quality": random.random(),
        "novelty": random.random(),
        "diversity": random.random(),
        "efficiency": random.random(),
        "cost": random.random()
    }


def mutate(strategy):
    return {k: max(0, min(1, v + random.uniform(-0.1, 0.1))) for k, v in strategy.items()}


def evaluate(strategy):
    score = (
        strategy["quality"] * 0.3 +
        strategy["novelty"] * 0.25 +
        strategy["diversity"] * 0.2 +
        strategy["efficiency"] * 0.15 -
        strategy["cost"] * 0.1
    )
    strategy["score"] = score
    write_metrics(strategy)
    return score


def create_artifact(strategy):
    aid = str(uuid.uuid4())
    path = f"{ARTIFACT_DIR}/{aid}"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/artifact.json", "w") as f:
        json.dump(strategy, f)
    log_event("artifact", {"id": aid})


def worker(_):

    strategy = random_strategy()

    strategy = mutate(strategy)

    score = evaluate(strategy)

    create_artifact(strategy)

    return score


def loop():

    workers = mp.cpu_count()

    pool = mp.Pool(workers)

    while True:

        scores = pool.map(worker, range(workers))

        print("tick", sum(scores) / len(scores))

        time.sleep(1)


if __name__ == "__main__":
    loop()
