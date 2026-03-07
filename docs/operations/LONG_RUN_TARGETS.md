# Long-Run Targets

## Profiles

- `smoke`: minimum 256 ticks, target 1,000 ticks
- `bootstrap`: minimum 1,000 ticks
- `aggressive`: minimum 5,000 ticks
- `soak`: minimum 50,000 ticks
- `production`: unbounded runtime until operator stop or guardrail stop

## Ecology Floors

- surviving lineages floor: 4 for bootstrap, 6 for aggressive, 8 for soak
- active domains floor: 3 for bootstrap, 4 for aggressive and soak
- preferred dominance ceiling: 0.35
- hard dominance intervention threshold: 0.50
- effective lineage diversity target: 0.55 or higher
- stability target: 0.70 or higher
- economy balance target: 0.65 or higher

## Replay Floors

- append-only violations: zero
- replay mismatches: zero
- replay digest/state reconstruction must remain stable across repeated replay of the same history
