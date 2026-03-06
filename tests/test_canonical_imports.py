import runtime.oed_orchestrator as canonical_oed
import runtime.policy_runtime as canonical_policy_runtime

from metaos.runtime.oed_orchestrator import step as legacy_step
from metaos.runtime.policy_runtime import evolve_policy as legacy_evolve_policy


def test_runtime_canonical_imports_resolve() -> None:
    assert callable(canonical_oed.step)
    assert callable(canonical_policy_runtime.evolve_policy)


def test_legacy_runtime_imports_resolve_to_canonical_exports() -> None:
    assert legacy_step is canonical_oed.step
    assert legacy_evolve_policy is canonical_policy_runtime.evolve_policy
