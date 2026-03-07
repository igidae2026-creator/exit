from __future__ import annotations

import hashlib
import stat
import sys
from pathlib import Path
from typing import Iterable

IMMUTABLE = {
    "docs/core/METAOS_CONSTITUTION.md",
    "docs/core/METAOS_MASTER_SPEC.md",
    "docs/00_METAOS_CONSTITUTION.md",
    "docs/01_METAOS_MASTER_SPEC.md",
}


def norm(path: str | Path) -> str:
    return str(Path(path).as_posix()).lstrip("./")


def _repo_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path(__file__).resolve().parents[1]).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return Path(__file__).resolve().parents[1]


def immutable_paths(repo_root: str | Path | None = None) -> dict[str, Path]:
    root = _repo_root(repo_root)
    candidates = {
        "docs/core/METAOS_CONSTITUTION.md": [root / "docs/core/METAOS_CONSTITUTION.md", root / "docs/00_METAOS_CONSTITUTION.md"],
        "docs/core/METAOS_MASTER_SPEC.md": [root / "docs/core/METAOS_MASTER_SPEC.md", root / "docs/01_METAOS_MASTER_SPEC.md"],
    }
    resolved: dict[str, Path] = {}
    for canonical, options in candidates.items():
        resolved[canonical] = next((path for path in options if path.exists()), options[0])
    return resolved


def check(paths: Iterable[str | Path]) -> None:
    blocked = [norm(path) for path in paths if norm(path) in IMMUTABLE]
    if blocked:
        raise PermissionError(f"immutable constitution file modification detected: {', '.join(blocked)}")


def assert_writable(paths: Iterable[str | Path]) -> None:
    check(paths)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_hash(path: Path) -> dict[str, str | bool]:
    hash_path = path.with_suffix(path.suffix + ".sha256")
    current = _sha256(path)
    if not hash_path.exists():
        return {"path": str(path), "ok": True, "sha256": current, "expected": current}
    expected = hash_path.read_text(encoding="utf-8").strip().split()[0]
    return {"path": str(path), "ok": current == expected, "sha256": current, "expected": expected}


def install_git_hook(repo_root: str | Path | None = None) -> dict[str, object]:
    root = _repo_root(repo_root)
    hooks_dir = root / ".git" / "hooks"
    if not hooks_dir.exists():
        return {"installed": False, "reason": "git_hooks_missing"}
    hook_path = hooks_dir / "pre-commit"
    script = "#!/bin/sh\npython3 -m validation.immutability $(git diff --cached --name-only)\n"
    existing = hook_path.read_text(encoding="utf-8") if hook_path.exists() else ""
    if existing != script:
        hook_path.write_text(script, encoding="utf-8")
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return {"installed": True, "hook": str(hook_path)}


def validate_constitution(repo_root: str | Path | None = None) -> dict[str, object]:
    root = _repo_root(repo_root)
    results = []
    for relative, path in immutable_paths(root).items():
        if not path.exists():
            raise FileNotFoundError(f"missing immutable document: {relative}")
        result = _validate_hash(path)
        if not bool(result["ok"]):
            raise RuntimeError(f"constitution hash mismatch: {relative}")
        results.append(result)
    hook = install_git_hook(root)
    return {"ok": True, "documents": results, "hook": hook}


if __name__ == "__main__":
    try:
        check(sys.argv[1:])
    except PermissionError as exc:
        print(f"BLOCKED: {exc}")
        sys.exit(1)
