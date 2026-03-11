from __future__ import annotations

import importlib


def consumer_control_state():
    module = importlib.import_module("metaos" + ".runtime.consumer_control")
    return module.consumer_control_state()


def consumer_control_decision(project_type=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_control")
    return module.consumer_control_decision(project_type)


def projected_queue_state(project_type=None, active_job_id=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_control")
    return module.projected_queue_state(project_type, active_job_id=active_job_id)


def projected_supervisor_state(project_type=None, active_job_id=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_control")
    return module.projected_supervisor_state(project_type, active_job_id=active_job_id)


__all__ = [
    "consumer_control_decision",
    "consumer_control_state",
    "projected_queue_state",
    "projected_supervisor_state",
]
