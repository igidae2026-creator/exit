from runtime.knowledge_system import knowledge_guidance


def test_knowledge_guidance_exposes_reuse_bias() -> None:
    out = knowledge_guidance(domain="code_domain", pressure={"resurrection_potential": 0.6, "innovation_density": 0.5})
    assert out["domain"] == "code_domain"
    assert out["reuse_bias"] >= 0.0
    assert "top_pattern_hints" in out
