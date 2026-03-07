from pathlib import Path

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


def test_runtime_composition_layers_do_not_import_deprecated_runtime_paths() -> None:
    forbidden = (
        "from metaos.runtime.",
        "import metaos.runtime.",
        "from kernel.",
        "import kernel.",
        "from core.",
        "import core.",
        "from evolution.",
        "import evolution.",
    )
    for path in sorted(Path("runtime").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden), str(path)


def test_domains_canonical_files_do_not_import_metaos_domains() -> None:
    for path in Path("domains").glob("domain_*.py"):
        text = path.read_text(encoding="utf-8")
        assert "from metaos.domains." not in text, str(path)
        assert "import metaos.domains." not in text, str(path)
