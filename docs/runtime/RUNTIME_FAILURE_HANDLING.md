# Runtime Failure Handling

## 1. Runtime Failure Categories
- invalid state transition
- replay divergence / unreadable logs
- invalid artifact envelope
- invalid domain contract
- loop break (no forward progress)
- repair failure escalation

## 2. Soft Failure Handling
Soft failures trigger bounded mitigation:
1. reduce worker pressure / rebalance budgets
2. inject exploration/reframing quest
3. log guardrail action to append-only stream

## 3. Hard Failure Handling
Hard failures require immediate containment:
1. switch supervisor mode to safe mode
2. restore replayable state from append-only truth
3. apply repair quest with escalation tracking
4. verify recovery within bounded ticks

## 4. Loop Break Recovery
If quest loop stalls:
- mark loop break in runtime safety surface
- force reframing or domain diversification quest
- prevent irreversible state writes until recovery criteria pass

## 5. Invalid Domain Response
- quarantine invalid domain generation
- keep historical artifacts immutable for audit
- continue execution with healthy domains
- require domain contract validation before reactivation

## 6. Invalid Artifact Response
- reject invalid envelope from canonical registries
- preserve raw record for forensics
- emit explicit failure event (no silent drop)

## 7. Escalation Rules
Escalate when repeated repair attempts exceed bounded retries:
- trigger repair escalation quest
- increase repair and replay budget share
- require replay-check success before returning to normal mode
