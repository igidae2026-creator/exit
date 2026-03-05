import time
from datetime import datetime, timezone
import json
import random


def write_metrics():
    metrics = {
        "quality": round(random.uniform(0.5, 1.0), 2),
        "novelty": round(random.uniform(0.5, 1.0), 2),
        "diversity": round(random.uniform(0.5, 1.0), 2),
        "efficiency": round(random.uniform(0.5, 1.0), 2),
        "cost": round(random.uniform(0.1, 0.9), 2),
    }

    score = sum(metrics.values()) / len(metrics)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "metrics",
        "payload": {**metrics, "score": round(score, 2)},
    }

    with open("metrics.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")


while True:
    write_metrics()
    time.sleep(2)
