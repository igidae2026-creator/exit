def log_event(event_type, payload):
    import json
    from datetime import datetime, timezone

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload
    }

    with open("events.jsonl","a") as f:
        f.write(json.dumps(event)+"\n")
