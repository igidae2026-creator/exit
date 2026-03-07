# Ownership Matrix

## Purpose

This document classifies every meaningful top-level surface as canonical, compatibility shim, release-only, repo-only, or runtime helper.

## Machine-Readable Source

- canonical manifest: `validation/ownership_manifest.json`
- loader: `validation/ownership_manifest.py`

## Canonical Packages

- `artifact/`: immutable artifacts, archive, registry, lineage, hydration accounting
- `domains/`: contracts and domain implementations
- `ecosystem/`: ecosystem discovery, clustering, market, knowledge network
- `federation/`: exchange, adoption, transport, hydration, replay support
- `genesis/`: append-only truth, replay, invariants, recovery
- `metaos/`: installed package and CLI owner
- `metaos_a/`, `metaos_b/`, `metaos_c/`: layered exploration runtime
- `observer/`: read-only runtime projections
- `runtime/`: civilization loop, orchestration, long-run validation
- `validation/`: boundary, artifact, ownership, and law checks

## Compatibility Shims

- `app/`: thin CLI forwarder to `metaos.cli`
- `core/`: deprecated import bridge to canonical runtime and artifact owners
- `kernel/`: deprecated bridge to `genesis/`
- `evolution/`: deprecated bridge to `runtime/`
- `setup.py`: compatibility shim for build tooling; `pyproject.toml` is canonical

## Runtime Helpers

- `loop/`: loop-model helpers used by runtime and tests
- `signal/`: pressure/signal helpers used by runtime and tests
- `strategy/`: selection and mutation helpers used by runtime and tests

## Release-Only Surfaces

- `docs/`: operator and architecture truth
- `ops/`: operator shell entrypoints and service helpers
- `scripts/`: release, validation, and packaging helpers
- `tests/`: shipped in source release for verification, not installed as packages

## Repo-Only Surfaces

- `metaos-build-prompts/`: Codex prompt-generation material
- `.github/`: CI workflows

## Invariants

- canonical owners own business logic
- compatibility shims remain tiny and honest
- read-only observer and `app/` surfaces must not gain runtime business logic
- release scripts and validators must consume the ownership manifest, not duplicate lists
- installed wheel must include every package required by the documented CLI runtime

## Test Mapping

- `tests/test_ownership_manifest.py`
- `tests/test_packaging_truth.py`
- `tests/test_release_tree.py`
- `tests/test_release_install.py`
- `tests/test_deprecated_surfaces_are_shims.py`
