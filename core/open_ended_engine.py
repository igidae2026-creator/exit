import json
import os
import uuid
import random
import time
from datetime import datetime, timezone

ARTIFACT_DIR = "artifact_store"


def now():
    return datetime.now(timezone.utc).isoformat()


def log_event(event_type, payload):
    event = {
        "timestamp": now(),
        "event_type": event_type,
        "payload": payload
    }
    with open("events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")


def write_metrics(metrics):
    event = {
        "timestamp": now(),
        "event_type": "metrics",
        "payload": metrics
    }
    with open("metrics.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")


def mutate_strategy(strategy):
    return {
        "quality": min(1.0, max(0.0, strategy["quality"] + random.uniform(-0.1, 0.1))),
        "novelty": min(1.0, max(0.0, strategy["novelty"] + random.uniform(-0.1, 0.1))),
        "diversity": min(1.0, max(0.0, strategy["diversity"] + random.uniform(-0.1, 0.1))),
        "efficiency": min(1.0, max(0.0, strategy["efficiency"] + random.uniform(-0.1, 0.1))),
        "cost": min(1.0, max(0.0, strategy["cost"] + random.uniform(-0.1, 0.1))),
    }


def create_artifact(strategy):
    artifact_id = str(uuid.uuid4())
    path = os.path.join(ARTIFACT_DIR, artifact_id)

    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "artifact.json"), "w") as f:
        json.dump(strategy, f)

    log_event("artifact_created", {"artifact_id": artifact_id})

    return artifact_id


def evaluate(strategy):
    score = (
        strategy["quality"] * 0.3 +
        strategy["novelty"] * 0.25 +
        strategy["diversity"] * 0.2 +
        strategy["efficiency"] * 0.15 -
        strategy["cost"] * 0.1
    )

    metrics = strategy.copy()
    metrics["score"] = round(score, 3)

    write_metrics(metrics)

    return score


def random_strategy():
    return {
        "quality": random.random(),
        "novelty": random.random(),
        "diversity": random.random(),
        "efficiency": random.random(),
        "cost": random.random()
    }


def loop():

    population = [random_strategy() for _ in range(5)]

    while True:

        new_population = []

        for strategy in population:

            mutated = mutate_strategy(strategy)

            create_artifact(mutated)

            score = evaluate(mutated)

            if score > 0.4:
                new_population.append(mutated)

        if len(new_population) < 3:
            new_population.append(random_strategy())

        population = new_population

        time.sleep(2)


if __name__ == "__main__":
    loop()
