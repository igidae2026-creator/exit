from __future__ import annotations

from typing import Mapping

from metaos.observer.metrics_history import failure_spike, novelty_drop, plateau
from metaos.registry.lineage_graph import concentration


def pressure(metrics: Mapping[str, float]) -> dict[str, float]:
    lc = concentration()
    p = {
        "novelty_pressure": max(0.0, 1.0 - float(metrics.get("novelty", 0.0))),
        "diversity_pressure": max(0.0, 1.0 - float(metrics.get("diversity", 0.0))),
        "efficiency_pressure": max(0.0, float(metrics.get("cost", 0.0))),
        "repair_pressure": max(0.0, float(metrics.get("fail_rate", 0.0))),
        "domain_shift_pressure": 0.0,
        "reframing_pressure": 0.0,
        "lineage_pressure": lc,
    }
    if plateau():
        p["domain_shift_pressure"] += 0.7
        p["reframing_pressure"] += 0.4
    if novelty_drop():
        p["novelty_pressure"] += 0.4
        p["reframing_pressure"] += 0.2
    if failure_spike():
        p["repair_pressure"] += 0.5
    if lc > 0.45:
        p["diversity_pressure"] += 0.5
        p["reframing_pressure"] += 0.3
    return p
