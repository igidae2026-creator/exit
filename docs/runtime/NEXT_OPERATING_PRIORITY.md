# Priority Queue: Highest-Value Runtime Work Next

## Read This When

You need to decide what runtime work is still worth doing next, without reopening settled architecture.

## Immediate Priority

1. `normal / hold / reject / escalate` operating report
2. longer cross-consumer soak and threshold calibration
3. rollout profile separation for different intervention sensitivity
4. top false-hold reasons relaxed before deeper redesign

## Why These Are Next

The core architecture is already mostly locked.

The highest remaining value is proving that the platform:

- routes routine cases without asking
- exposes operational ratios clearly
- survives failure and replay pressure
- tunes intervention thresholds against false hold / reject / escalate

These priorities should still be evaluated under higher MetaOS law:

- `exploration OS`
- `lineage`
- `replayability`
- `append-only truth`

## Selection Rule

Prefer platform operating truth over new design prose.

If a new document does not improve:

- rollout safety
- compatibility visibility
- failure recovery
- consumer onboarding speed
- threshold calibration visibility

it is lower priority than code or tests.

Reference:
- `docs/runtime/RUNTIME_DOCS_INDEX.md`
- `docs/runtime/PLATFORM_LAYER_FRAMING.md`
- `docs/runtime/HUMAN_INTERVENTION_THRESHOLD.md`
