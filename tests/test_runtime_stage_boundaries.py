from runtime.orchestration.civilization_stage import build_civilization_frame
from runtime.orchestration.economy_stage import build_economy_frame
from runtime.orchestration.pressure_stage import build_pressure_frame
from runtime.orchestration.selection_stage import build_selection_frame


def test_runtime_stages_return_bounded_frames() -> None:
    pressure = build_pressure_frame(
        {"score": 0.5, "novelty": 0.2, "diversity": 0.3, "cost": 0.2, "fail_rate": 0.1},
        domain="default",
        history=[],
        plateau_fn=lambda: False,
        novelty_drop_fn=lambda: False,
        concentration_fn=lambda: 0.1,
    )
    ecology = {"novelty_health": 0.5, "diversity_health": 0.5, "efficiency_health": 0.5, "lineage_health": 0.5, "repair_health": 0.5, "exploration_health": 0.5}
    civilization = build_civilization_frame([], {"population_counts": {}}, ecology)
    economy = build_economy_frame(pressure["stabilized_pressure"], ecology, {"population_counts": {}}, civilization["memory_state"], {"workers": 4, "effective_workers": 4})
    selection = build_selection_frame(pressure["stabilized_pressure"], {"mutation_bias": 0.2, "selection_bias": 0.2}, ecology, {"population_counts": {}}, {"intervention": False}, tick=1)
    assert set(pressure) >= {"pressure", "stabilized_pressure", "guard"}
    assert set(civilization) >= {"civilization_state", "memory_state", "civilization_stability"}
    assert set(economy) >= {"economy", "resource_allocation", "budgets"}
    assert set(selection) >= {"civilization_selection"}
