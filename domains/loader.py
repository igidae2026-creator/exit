from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


def load_domain(name: str) -> Any:
    normalized = str(name).replace("-", "_")
    package_runtime = Path(__file__).resolve().parent / normalized / "runtime.py"
    if package_runtime.exists():
        spec = importlib.util.spec_from_file_location(f"domains.{normalized}.runtime_pkg", package_runtime)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    return importlib.import_module(f"domains.{normalized}")
