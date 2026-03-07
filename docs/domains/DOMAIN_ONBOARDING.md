# Domain Onboarding

## Goal

Admit new domains without modifying the minimal core.

## Requirements

- implement the domain contract
- provide genome, mutation, and recombination compatibility
- define evaluators and safety bounds in the domain layer
- register through loader/onboarding paths, not by editing `genesis/`

## Lifecycle

- created
- active
- inactive
- retired
- resurrectable

## Acceptance

- domain appears in discovery
- domain contributes to lineage ecology without monopolizing selection
- replay reconstructs domain lifecycle state
