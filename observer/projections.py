from __future__ import annotations

from typing import Any, Mapping

from kernel.replay import replay_state


def status_projection() -> dict[str, Any]:
    return replay_state()

