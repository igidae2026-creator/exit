"""Repository-local build backend for clean wheel truth."""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib
import io
import json
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import tomllib


REPO_ROOT = Path(__file__).resolve().parent
OWNERSHIP_MANIFEST = REPO_ROOT / "validation" / "ownership_manifest.json"


def _maybe_setuptools():
    try:
        return importlib.import_module("setuptools.build_meta")
    except ModuleNotFoundError:
        return None


_SETUPTOOLS = _maybe_setuptools()


def _project_table() -> dict[str, Any]:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return dict(data.get("project", {}))


def _manifest_rows() -> list[dict[str, Any]]:
    payload = json.loads(OWNERSHIP_MANIFEST.read_text(encoding="utf-8"))
    return [dict(row) for row in payload.get("paths", []) if isinstance(row, dict)]


def _packaged_roots() -> list[str]:
    return [str(row["path"]) for row in _manifest_rows() if bool(row.get("packaged"))]


def _release_paths() -> list[str]:
    return [str(row["path"]) for row in _manifest_rows() if bool(row.get("release_included"))]


def _distribution_name() -> str:
    return str(_project_table()["name"])


def _version() -> str:
    return str(_project_table()["version"])


def _wheel_filename() -> str:
    return f"{_distribution_name()}-{_version()}-py3-none-any.whl"


def _dist_info_dirname() -> str:
    return f"{_distribution_name()}-{_version()}.dist-info"


def _metadata_text() -> str:
    project = _project_table()
    lines = [
        "Metadata-Version: 2.1",
        f"Name: {project['name']}",
        f"Version: {project['version']}",
    ]
    readme = project.get("readme")
    if readme:
        lines.append(f"Description-Content-Type: text/markdown")
    for dependency in project.get("dependencies", []):
        lines.append(f"Requires-Dist: {dependency}")
    optional = project.get("optional-dependencies", {})
    for group, deps in sorted(optional.items()):
        for dep in deps:
            lines.append(f"Requires-Dist: {dep} ; extra == '{group}'")
    return "\n".join(lines) + "\n"


def _entry_points_text() -> str:
    scripts = dict(_project_table().get("scripts", {}))
    if not scripts:
        return ""
    body = ["[console_scripts]"]
    for name, target in sorted(scripts.items()):
        body.append(f"{name} = {target}")
    return "\n".join(body) + "\n"


def _wheel_text() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: metaos.build_backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )


def _hash_bytes(payload: bytes) -> str:
    digest = hashlib.sha256(payload).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _package_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for root_name in _packaged_roots():
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            files.append((path, path.relative_to(REPO_ROOT).as_posix()))
    return files


def _sdist_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for relative in _release_paths() + ["build_backend.py"]:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if not child.is_file():
                    continue
                if "__pycache__" in child.parts or child.suffix in {".pyc", ".pyo"}:
                    continue
                target = child.relative_to(REPO_ROOT).as_posix()
                if target not in seen:
                    seen.add(target)
                    files.append((child, target))
            continue
        target = path.relative_to(REPO_ROOT).as_posix()
        if target not in seen:
            seen.add(target)
            files.append((path, target))
    return files


def _write_metadata_dir(target_dir: Path) -> str:
    dist_info = target_dir / _dist_info_dirname()
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    (dist_info / "WHEEL").write_text(_wheel_text(), encoding="utf-8")
    entry_points = _entry_points_text()
    if entry_points:
        (dist_info / "entry_points.txt").write_text(entry_points, encoding="utf-8")
    return dist_info.name


def _build_wheel_fallback(wheel_directory: str, metadata_directory: str | None = None) -> str:
    wheel_dir = Path(wheel_directory)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = wheel_dir / _wheel_filename()
    dist_info = _dist_info_dirname()
    records: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for source, arcname in _package_files():
            payload = source.read_bytes()
            zf.writestr(arcname, payload)
            records.append((arcname, _hash_bytes(payload), str(len(payload))))

        metadata = _metadata_text().encode("utf-8")
        wheel_text = _wheel_text().encode("utf-8")
        zf.writestr(f"{dist_info}/METADATA", metadata)
        zf.writestr(f"{dist_info}/WHEEL", wheel_text)
        records.append((f"{dist_info}/METADATA", _hash_bytes(metadata), str(len(metadata))))
        records.append((f"{dist_info}/WHEEL", _hash_bytes(wheel_text), str(len(wheel_text))))

        entry_points = _entry_points_text()
        if entry_points:
            payload = entry_points.encode("utf-8")
            zf.writestr(f"{dist_info}/entry_points.txt", payload)
            records.append((f"{dist_info}/entry_points.txt", _hash_bytes(payload), str(len(payload))))

        record_path = f"{dist_info}/RECORD"
        record_buffer = io.StringIO()
        writer = csv.writer(record_buffer, lineterminator="\n")
        for row in records:
            writer.writerow(row)
        writer.writerow((record_path, "", ""))
        record_payload = record_buffer.getvalue().encode("utf-8")
        zf.writestr(record_path, record_payload)
    return wheel_path.name


def _build_editable_fallback(wheel_directory: str, metadata_directory: str | None = None) -> str:
    wheel_dir = Path(wheel_directory)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = wheel_dir / _wheel_filename()
    dist_info = _dist_info_dirname()
    project_root_pth = f"{_distribution_name()}.pth"
    records: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        pth_payload = f"{REPO_ROOT.as_posix()}\n".encode("utf-8")
        zf.writestr(project_root_pth, pth_payload)
        records.append((project_root_pth, _hash_bytes(pth_payload), str(len(pth_payload))))

        metadata = _metadata_text().encode("utf-8")
        wheel_text = _wheel_text().encode("utf-8")
        zf.writestr(f"{dist_info}/METADATA", metadata)
        zf.writestr(f"{dist_info}/WHEEL", wheel_text)
        records.append((f"{dist_info}/METADATA", _hash_bytes(metadata), str(len(metadata))))
        records.append((f"{dist_info}/WHEEL", _hash_bytes(wheel_text), str(len(wheel_text))))

        entry_points = _entry_points_text()
        if entry_points:
            payload = entry_points.encode("utf-8")
            zf.writestr(f"{dist_info}/entry_points.txt", payload)
            records.append((f"{dist_info}/entry_points.txt", _hash_bytes(payload), str(len(payload))))

        record_path = f"{dist_info}/RECORD"
        record_buffer = io.StringIO()
        writer = csv.writer(record_buffer, lineterminator="\n")
        for row in records:
            writer.writerow(row)
        writer.writerow((record_path, "", ""))
        record_payload = record_buffer.getvalue().encode("utf-8")
        zf.writestr(record_path, record_payload)
    return wheel_path.name


def _build_sdist_fallback(sdist_directory: str) -> str:
    sdist_dir = Path(sdist_directory)
    sdist_dir.mkdir(parents=True, exist_ok=True)
    base = f"{_distribution_name()}-{_version()}"
    archive_name = f"{base}.tar.gz"
    archive_path = sdist_dir / archive_name
    with tarfile.open(archive_path, "w:gz") as tf:
        for source, relative in _sdist_files():
            tf.add(source, arcname=f"{base}/{relative}")
    return archive_name


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    if _SETUPTOOLS is not None:
        return _SETUPTOOLS.build_wheel(wheel_directory, config_settings, metadata_directory)
    return _build_wheel_fallback(wheel_directory, metadata_directory)


def build_sdist(sdist_directory: str, config_settings: dict[str, Any] | None = None) -> str:
    if _SETUPTOOLS is not None:
        return _SETUPTOOLS.build_sdist(sdist_directory, config_settings)
    return _build_sdist_fallback(sdist_directory)


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    if _SETUPTOOLS is not None:
        return _SETUPTOOLS.prepare_metadata_for_build_wheel(metadata_directory, config_settings)
    return _write_metadata_dir(Path(metadata_directory))


def get_requires_for_build_wheel(config_settings: dict[str, Any] | None = None) -> list[str]:
    if _SETUPTOOLS is not None:
        return list(_SETUPTOOLS.get_requires_for_build_wheel(config_settings))
    return []


def get_requires_for_build_sdist(config_settings: dict[str, Any] | None = None) -> list[str]:
    if _SETUPTOOLS is not None:
        return list(_SETUPTOOLS.get_requires_for_build_sdist(config_settings))
    return []


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    if _SETUPTOOLS is not None and hasattr(_SETUPTOOLS, "build_editable"):
        return _SETUPTOOLS.build_editable(wheel_directory, config_settings, metadata_directory)
    return _build_editable_fallback(wheel_directory, metadata_directory)


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    if _SETUPTOOLS is not None and hasattr(_SETUPTOOLS, "prepare_metadata_for_build_editable"):
        return _SETUPTOOLS.prepare_metadata_for_build_editable(metadata_directory, config_settings)
    return _write_metadata_dir(Path(metadata_directory))


def get_requires_for_build_editable(config_settings: dict[str, Any] | None = None) -> list[str]:
    if _SETUPTOOLS is not None and hasattr(_SETUPTOOLS, "get_requires_for_build_editable"):
        return list(_SETUPTOOLS.get_requires_for_build_editable(config_settings))
    return []
