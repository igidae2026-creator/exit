from __future__ import annotations

import importlib


def recommended_interventions(report=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.recommended_interventions(report)


def threshold_profile(profile="balanced"):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.threshold_profile(profile)


def default_profile_for_consumer(project_type=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.default_profile_for_consumer(project_type)


def consumer_family_for(project_type=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.consumer_family_for(project_type)


def resolve_profile(profile=None, project_type=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.resolve_profile(profile, project_type=project_type)


def intervention_status():
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.intervention_status()


def apply_interventions(report=None):
    module = importlib.import_module("metaos" + ".runtime.consumer_interventions")
    return module.apply_interventions(report)


__all__ = [
    "apply_interventions",
    "consumer_family_for",
    "default_profile_for_consumer",
    "intervention_status",
    "recommended_interventions",
    "resolve_profile",
    "threshold_profile",
]
