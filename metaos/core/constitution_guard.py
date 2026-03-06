from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


class ConstitutionViolation(RuntimeError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[2]
IMMUTABLE_DOCS = (
    REPO_ROOT / "docs" / "METAOS_CONSTITUTION.md",
    REPO_ROOT / "docs" / "METAOS_MASTER_SPEC.md",
)
EXPECTED_HASHES = {
    "METAOS_CONSTITUTION.md": "0cddeb1d363da1ae35593b5c623b9c9fa2770a2a3ec8ea9431814a636698c786",
    "METAOS_MASTER_SPEC.md": "fca2685fc9baa00f751761e5349b2322950b3ba4439cee781874f7808696d673",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def immutable_docs() -> tuple[Path, Path]:
    return IMMUTABLE_DOCS


def validate_constitution() -> None:
    for path in IMMUTABLE_DOCS:
        if not path.exists():
            raise ConstitutionViolation(f"immutable document missing: {path}")
        expected = EXPECTED_HASHES.get(path.name)
        if expected and _sha256(path) != expected:
            raise ConstitutionViolation(f"immutable document modified: {path}")


def assert_writable(targets: Iterable[str | Path]) -> None:
    protected = {path.resolve() for path in IMMUTABLE_DOCS}
    for target in targets:
        path = Path(target).resolve()
        if path in protected:
            raise ConstitutionViolation(f"writes to immutable constitutional document are forbidden: {path}")


def protect_write(target: str | Path) -> None:
    assert_writable([target])
    validate_constitution()
