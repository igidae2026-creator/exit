# Genesis Gap Matrix

| Theme | Observed Gap | Remediation |
| --- | --- | --- |
| Loop coherence | Orchestrator and validator had duplicated contradictory logic | Replaced with single canonical implementations |
| Runtime autonomy | Production path could be silently collapsed by broken defaults | `production` profile is explicitly unbounded by default |
| Append-only truth | Replay surfaces existed, but validation reporting was inconsistent | Long-run validator now reports replay, append-only, and mismatch counts coherently |
| Artifact law | Required fields existed but law reporting was shallow | Validation now reports replayability, provenance presence, and lineage tracking |
| Boundary law | Human/system boundary module was malformed | Rebuilt using canonical expected role sets |
| Policy runtime | Policy evolution existed but reporting path was broken | Long-run validator surfaces policy generations and profile acceptance |
| Ecology floors | Tier/profile floors were inconsistent across docs and code | Floors aligned around smoke/bootstrap/aggressive/soak/production targets |
| Operator truth | Mandatory audit/remediation docs were absent | Added audit, contradiction, targets, quickstart, and failure protocol docs |
| Release truth | Release validator did not require remediation truth files | Release validation now checks mandatory report and architecture docs |
