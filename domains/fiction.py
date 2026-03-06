from __future__ import annotations

from domains.domain_genome import canonical_domain_genome


def generate() -> dict[str, float]:
    return canonical_domain_genome("fiction").seed_strategy
