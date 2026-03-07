# Deprecation And Compatibility

## Canonical Surfaces

- `genesis/`
- `runtime/`
- `artifact/`
- `domains/`
- `validation/`
- `metaos/`
- `metaos_a/`, `metaos_b/`, `metaos_c/`

## Compatibility Surfaces

- `app/`
- `core/`
- `kernel/`
- `evolution/`
- `loop/`
- `metaos/kernel/`
- `metaos/runtime/`
- `metaos/domains/`

## Rules

- Shims forward or mirror canonical behavior only.
- New operators should target `metaos` or `python -m app.cli`, not compatibility imports.
- Deprecation does not mean removal from release truth; it means no new ownership of business logic.
