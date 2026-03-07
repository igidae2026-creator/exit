# Ownership and Release Matrix

`release_manifest.json` is the single machine-readable source of truth for ownership classification and release inclusion.

## Canonical public packages

- `metaos` (primary CLI and package owner)
- `artifact`
- `domains`
- `genesis`
- `metaos_a`, `metaos_b`, `metaos_c`
- `runtime`
- `validation`

## Compatibility/deprecated shims

- `app` remains a compatibility CLI shim that forwards to `metaos.cli`.
- `core`, `kernel`, and `evolution` are deprecated compatibility surfaces and do not own new business logic.

## Runtime helpers and repo-only surfaces

- Runtime helper (not packaged): `observer`, `signal`, `strategy`, `loop`, `federation`.
- Repo-only contributor assets: `metaos-build-prompts`, `ecosystem`.
- Release-only ops/support assets: `ops`, `scripts`, `docs`, `tests`.

## Validation contract

- `scripts/build_release_zip.sh` and `scripts/validate_release_tree.sh` both consume `release_manifest.json`.
- Tests assert packaging metadata and release validation remain synchronized with this manifest.
