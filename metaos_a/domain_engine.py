from __future__ import annotations

from typing import Any

from artifact.registry import register_envelope
from domains.loader import load_domain
from genesis.spine import append_event, append_metrics
from metaos_a.domain_resources import load_resources
from metaos_a.domain_state import DomainState


class DomainEngine:
    def __init__(self, goal: str, domain_name: str) -> None:
        self.goal = str(goal)
        self.domain_name = str(domain_name)
        self.runtime = load_domain(domain_name)
        self.state = DomainState(goal=self.goal, domain_name=self.domain_name)

    def step(self) -> dict[str, Any]:
        self.state.tick += 1
        signal = self.runtime.input()
        artifact = self.runtime.generate()
        evaluation = self.runtime.evaluate(artifact)
        metrics = self.runtime.metrics(artifact)
        loop = self.runtime.loop()
        artifact_id = register_envelope(
            aclass="output",
            atype="output",
            spec={
                "goal": self.goal,
                "domain": self.domain_name,
                "signal": signal,
                "artifact": artifact,
                "evaluation": evaluation,
                "metrics": metrics,
                "loop": loop,
                "resources": self.runtime.resources(),
                "genome": self.runtime.genome(),
            },
            provenance={"score": float(evaluation.get("score", 0.0))},
        )
        append_event("metaos_a_tick", {"tick": self.state.tick, "domain": self.domain_name, "artifact_id": artifact_id})
        append_metrics({"tick": self.state.tick, **dict(metrics), "routing": {"selected_domain": self.domain_name}, "quest": {"type": "exploration"}})
        self.state.artifact_ids.append(artifact_id)
        self.state.lineage_counts[self.domain_name] = self.state.lineage_counts.get(self.domain_name, 0) + 1
        self.state.last_metrics = dict(metrics)
        self.state.last_output = {
            "artifact_id": artifact_id,
            "signal": signal,
            "artifact": artifact,
            "evaluation": evaluation,
            "metrics": metrics,
            "loop": loop,
            "resources": load_resources(self.runtime),
        }
        return dict(self.state.last_output)


__all__ = ["DomainEngine"]
