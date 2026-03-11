from __future__ import annotations

from pathlib import Path


CANONICAL_DOCS = {
    "docs/runtime/REPLAY_STATE_SPEC.md": ("## Purpose", "## Scope", "## Invariants", "## Inputs", "## Outputs", "## Failure Modes", "## Recovery Behavior", "## Ownership", "## Test Mapping", "## Operator Examples"),
    "docs/runtime/STATE_DERIVATION_SPEC.md": ("## Purpose", "## Scope", "## Invariants", "## Inputs", "## Outputs", "## Failure Modes", "## Recovery Behavior", "## Ownership", "## Test Mapping", "## Operator Examples"),
    "docs/runtime/SUPERVISOR_SPEC.md": ("## Purpose", "## Scope", "## Invariants", "## Inputs", "## Outputs", "## Failure Modes", "## Recovery Behavior", "## Ownership", "## Test Mapping", "## Operator Examples"),
    "docs/runtime/RUNTIME_FAILURE_HANDLING.md": ("## Purpose", "## Scope", "## Invariants", "## Inputs", "## Outputs", "## Failure Modes", "## Recovery Behavior", "## Ownership", "## Test Mapping", "## Operator Examples"),
    "docs/ops/OPERATIONS.md": ("# Operations",),
    "docs/ops/OPERATIONAL_AUTONOMY_STATUS.md": ("# Operational Autonomy Status",),
    "docs/ops/RECOVERY.md": ("# Recovery",),
    "docs/ops/RELEASE.md": ("# Release",),
    "docs/architecture/OWNERSHIP_MATRIX.md": ("## Purpose", "## Machine-Readable Source", "## Canonical Packages", "## Compatibility Shims", "## Release-Only Surfaces", "## Repo-Only Surfaces", "## Invariants", "## Test Mapping"),
}


def test_canonical_docs_are_not_placeholder_shells() -> None:
    for path, headings in CANONICAL_DOCS.items():
        text = Path(path).read_text(encoding="utf-8")
        for heading in headings:
            assert heading in text, f"{path}: missing {heading}"
        assert len([line for line in text.splitlines() if line.strip()]) >= 12, path
        assert "This document defines" not in text or len(text.split()) > 80, path
