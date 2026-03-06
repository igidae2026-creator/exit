from metaos.runtime.repair_system import choose_repair


def test_repair_system_prefers_checkpoint_restore_for_high_fail_rate() -> None:
    repair = choose_repair({"fail_rate": 0.9, "cost": 0.1}, {"repair_pressure": 0.95, "lineage_pressure": 0.2})
    assert repair == "checkpoint_restore"


def test_repair_system_uses_export_freeze_for_lineage_pressure() -> None:
    repair = choose_repair({"fail_rate": 0.4, "cost": 0.2}, {"repair_pressure": 0.7, "lineage_pressure": 0.8})
    assert repair == "export_freeze"
