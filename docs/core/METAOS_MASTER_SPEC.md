# METAOS MASTER SPEC

METAOS는 개인용 자율 탐색 운영체계다.

Loop:

signal → strategy → artifact → metrics → strategy

## Architecture

METAOS
├ kernel
├ loop
├ signal
├ domains
├ strategy
├ artifact
├ data
├ observer
└ validation

## Kernel

Kernel은 중앙 제어 시스템이다.

구성:

- State Machine
- Policy Engine
- Loop Controller
- Validation Manager
- Runtime Dispatcher

Kernel은 domain logic을 실행하지 않는다.

## Loop Model

Exploration
Ceiling Detection
Stabilization
Monitoring
Re-Exploration

## Data Model

Source of Truth

events.jsonl
metrics.jsonl
artifact_registry.jsonl

Derived

state.json