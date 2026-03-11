# Operating Report: What The Runtime Must Measure

## Read This When

You need to know what runtime operating truth must be visible before intervention, threshold tuning, or profile selection.

## Required Report Surface

The operating report should expose:

- verdict distribution
- hold top reasons
- reject top patterns
- escalate rate
- migration queue
- consumer health rollup

The report is derived from consumer lifecycle ledger records, not ad-hoc operator notes.

It should also expose:

- default profile mapping
- conformance matrix state
- migration queue visibility

Reference:
- `docs/runtime/RUNTIME_DOCS_INDEX.md`
- `docs/runtime/CONSUMER_INTERVENTIONS.md`
