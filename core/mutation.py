from __future__ import annotations

from random import Random
from typing import Mapping

from core.strategy_genome import StrategyGenome


def perturb(
    genome: StrategyGenome,
    *,
    scale: float = 0.1,
    rng: Random | None = None,
) -> StrategyGenome:
    """Apply gaussian noise to eval axis weights."""
    generator = rng or Random()
    mutated = {
        axis: float(value) + generator.gauss(0.0, scale)
        for axis, value in genome.eval_axes.items()
    }
    return StrategyGenome.create(
        domain=genome.domain,
        eval_axes=mutated,
        mutation_ops=genome.mutation_ops,
        budget=genome.budget,
        parent=genome.id,
    )


def swap(
    genome: StrategyGenome,
    *,
    rng: Random | None = None,
) -> StrategyGenome:
    """Swap two axis values to preserve magnitudes while changing priority."""
    generator = rng or Random()
    keys = list(genome.eval_axes.keys())
    if len(keys) < 2:
        return StrategyGenome.create(
            domain=genome.domain,
            eval_axes=genome.eval_axes,
            mutation_ops=genome.mutation_ops,
            budget=genome.budget,
            parent=genome.id,
        )

    i, j = generator.sample(range(len(keys)), 2)
    k1, k2 = keys[i], keys[j]
    mutated = dict(genome.eval_axes)
    mutated[k1], mutated[k2] = mutated[k2], mutated[k1]

    return StrategyGenome.create(
        domain=genome.domain,
        eval_axes=mutated,
        mutation_ops=genome.mutation_ops,
        budget=genome.budget,
        parent=genome.id,
    )


def recombine(
    left: StrategyGenome,
    right: StrategyGenome,
    *,
    rng: Random | None = None,
) -> StrategyGenome:
    """Create child genome by mixing fields from two parents."""
    generator = rng or Random()
    all_axes = set(left.eval_axes) | set(right.eval_axes)
    eval_axes: dict[str, float] = {}
    for axis in all_axes:
        choose_left = generator.random() < 0.5
        if choose_left and axis in left.eval_axes:
            eval_axes[axis] = left.eval_axes[axis]
        elif axis in right.eval_axes:
            eval_axes[axis] = right.eval_axes[axis]
        else:
            eval_axes[axis] = left.eval_axes[axis]

    domain = left.domain if generator.random() < 0.5 else right.domain
    mutation_ops = list(dict.fromkeys(left.mutation_ops + right.mutation_ops))
    budget = (left.budget + right.budget) / 2.0

    return StrategyGenome.create(
        domain=domain,
        eval_axes=eval_axes,
        mutation_ops=mutation_ops,
        budget=budget,
        parent=f"{left.id},{right.id}",
    )


def mutate(
    genome: StrategyGenome,
    op: str,
    *,
    pool: Mapping[str, StrategyGenome] | None = None,
    rng: Random | None = None,
) -> StrategyGenome:
    """Dispatch mutation operation by name."""
    if op == "perturb":
        return perturb(genome, rng=rng)
    if op == "swap":
        return swap(genome, rng=rng)
    if op == "recombine":
        if not pool:
            raise ValueError("recombine requires a non-empty pool")
        generator = rng or Random()
        partner = generator.choice(list(pool.values()))
        return recombine(genome, partner, rng=generator)

    raise ValueError(f"Unsupported mutation op: {op}")


__all__ = ["perturb", "swap", "recombine", "mutate"]
