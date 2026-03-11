from __future__ import annotations

from typing import Any, Dict, Tuple


MigrationKey = Tuple[str, str]
_MIGRATIONS: Dict[MigrationKey, Dict[str, Any]] = {}


def register_migration_rule(
    from_version: str,
    to_version: str,
    *,
    strategy: str,
    steps: list[str],
    compatibility_window: str = "bounded",
) -> None:
    _MIGRATIONS[(str(from_version), str(to_version))] = {
        "from_version": str(from_version),
        "to_version": str(to_version),
        "strategy": str(strategy),
        "steps": list(steps),
        "compatibility_window": str(compatibility_window),
    }


def clear_migration_rules() -> None:
    _MIGRATIONS.clear()


def migration_rule(from_version: str, to_version: str) -> Dict[str, Any] | None:
    return _MIGRATIONS.get((str(from_version), str(to_version)))


def migration_plan(from_version: str, to_version: str) -> Dict[str, Any]:
    rule = migration_rule(from_version, to_version)
    if rule is None:
        return {
            "available": False,
            "from_version": str(from_version),
            "to_version": str(to_version),
            "strategy": None,
            "steps": [],
            "compatibility_window": None,
        }
    return {"available": True, **rule}
