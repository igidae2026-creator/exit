from __future__ import annotations

from pathlib import Path


REQUIRED_DOCS = [
    "AGENTS.md",
    "AUDIT_MANIFEST.md",
    "GENESIS_GAP_MATRIX.md",
    "ARCHITECTURE_CONTRADICTIONS.md",
    "LONG_RUN_TARGETS.md",
    "FINAL_REMEDIATION_REPORT.md",
    "docs/architecture/CANONICAL_IMPORT_GRAPH.md",
    "docs/architecture/LOOP_CANONICALIZATION.md",
    "docs/operations/LONG_RUN_TARGETS.md",
    "docs/operations/DEPRECATION_AND_COMPATIBILITY.md",
    "docs/operations/OPERATOR_QUICKSTART.md",
    "docs/runtime/STATE_MODEL.md",
    "docs/runtime/FAILURE_PROTOCOL.md",
    "docs/runtime/POLICY_RUNTIME.md",
    "docs/domains/DOMAIN_ONBOARDING.md",
]


def test_required_remediation_docs_exist_and_are_nontrivial() -> None:
    for path in REQUIRED_DOCS:
        text = Path(path).read_text(encoding="utf-8")
        assert len(text.split()) >= 20, path


def test_docs_do_not_embed_local_absolute_paths() -> None:
    for path in REQUIRED_DOCS + ["README.md", "RUNBOOK.md"]:
        text = Path(path).read_text(encoding="utf-8")
        assert "/home/" not in text, path
        assert "file://" not in text, path
