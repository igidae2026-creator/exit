from __future__ import annotations

import os
import time

from core.constitution_guard import validate_constitution
from core.kernel_adapter import KernelAdapter
from core.replay import replay_state
from core.supervisor import Supervisor


def main() -> int:
    validate_constitution()
    adapter = KernelAdapter()
    supervisor = Supervisor(adapter)
    max_ticks = int(os.getenv("METAOS_MAX_TICKS", "0") or "0")
    tick_count = 0
    try:
        while True:
            state = replay_state("data")
            report = supervisor.run_cycle(state)
            tick_count += 1
            print(report, flush=True)
            if max_ticks and tick_count >= max_ticks:
                break
            time.sleep(float(os.getenv("METAOS_TICK_SECONDS", "1.0")))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
