from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping


DEFAULT_LOG = ".metaos_runtime/data/events.jsonl"
LOG = Path(os.environ.get("METAOS_EVENT_LOG", DEFAULT_LOG))
LOG.parent.mkdir(parents=True, exist_ok=True)


def emit(event_type: str, payload: Mapping[str, Any]) -> None:
    rec = {"t": time.time(), "type": event_type, "payload": dict(payload)}
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
