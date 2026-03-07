from runtime.knowledge_system import accumulated_knowledge, knowledge_guidance
from runtime.quest_ecology import generate_quest_portfolio
from runtime.replay_state import ReplayState


def test_knowledge_guidance_exposes_reuse_bias() -> None:
    out = knowledge_guidance(domain="code_domain", pressure={"resurrection_potential": 0.6, "innovation_density": 0.5})
    assert out["domain"] == "code_domain"
    assert out["reuse_bias"] >= 0.0
    assert "top_pattern_hints" in out


def test_accumulated_knowledge_and_quest_portfolio_use_active_replay_context() -> None:
    replay = ReplayState(
        artifacts={"a1": {"artifact_id": "a1", "artifact_type": "strategy", "domain": "code_domain", "lineage_id": "alpha"}},
        metric_history=[{"tick": 1.0, "score": 0.4}],
        tick_summaries=[{"tick": 1}],
        lineages={"alpha": 1},
        domain_counts={"code_domain": 1},
    )
    knowledge = accumulated_knowledge(replay=replay, civilization={"created_domains": ["code_domain"]})
    assert knowledge["references"] == {"artifacts": 1, "metrics": 1, "events": 1}
    portfolio = generate_quest_portfolio(replay, {"novelty_pressure": 0.8}, max_quests=1)
    assert portfolio[0]["knowledge"] == {"artifacts": 1, "metrics": 1, "events": 1}
