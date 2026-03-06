from __future__ import annotations

from typing import Any, Mapping

from kernel.contracts import DispatchFrame


def dispatch(
    *,
    tick: int,
    phase: str,
    quest_ids: list[str] | tuple[str, ...] = (),
    policy_id: str | None = None,
    parent_artifact_ids: list[str] | tuple[str, ...] = (),
    quota_frame: Mapping[str, Any] | None = None,
) -> DispatchFrame:
    return DispatchFrame(
        tick=int(tick),
        phase=str(phase),
        quest_ids=tuple(str(value) for value in quest_ids),
        policy_id=None if policy_id is None else str(policy_id),
        parent_artifact_ids=tuple(str(value) for value in parent_artifact_ids),
        quota_frame=None if quota_frame is None else quota_frame,  # type: ignore[arg-type]
    )


__all__ = ["dispatch"]
