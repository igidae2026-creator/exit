from __future__ import annotations

from runtime.orchestrator import Orchestrator, OrchestratorConfig


def main() -> None:
    orchestrator = Orchestrator(OrchestratorConfig.from_env())
    orchestrator.run()


if __name__ == "__main__":
    main()
