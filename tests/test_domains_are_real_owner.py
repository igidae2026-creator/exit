from pathlib import Path


def test_domains_real_owner_files_are_not_metaos_domain_wrappers() -> None:
    for relpath in (
        "domains/domain_crossbreed.py",
        "domains/domain_genome_mutation.py",
        "domains/domain_recombination.py",
    ):
        text = Path(relpath).read_text(encoding="utf-8")
        assert "from metaos.domains." not in text, relpath
        assert "import metaos.domains." not in text, relpath
