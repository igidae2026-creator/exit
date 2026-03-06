from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any


def _missing(*args: Any, **kwargs: Any) -> Any:
    raise RuntimeError("genesis compatibility shim target is unavailable")


def _load_target(name: str) -> ModuleType | None:
    for candidate in (f"metaos.kernel.{name}", f"kernel.{name}"):
        try:
            return importlib.import_module(candidate)
        except ModuleNotFoundError:
            continue
    return None


def _export_module(name: str) -> dict[str, Any]:
    module = _load_target(name)
    if module is None:
        return {"__all__": [], "_missing": _missing}
    names = getattr(module, "__all__", None)
    if not names:
        names = [key for key in vars(module) if not key.startswith("_")]
    exported = {key: getattr(module, key) for key in names}
    exported["__all__"] = list(names)
    return exported


__all__ = [
    "_export_module",
    "_load_target",
    "_missing",
]
