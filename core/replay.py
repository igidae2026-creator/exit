import json


def replay():
    events = []

    with open("events.jsonl") as f:
        for line in f:
            events.append(json.loads(line))

    return events
