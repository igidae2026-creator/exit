from setuptools import find_packages, setup

setup(
    name="metaos",
    version="0.0.0",
    packages=find_packages(
        where=".",
        include=[
            "app",
            "artifact",
            "domains",
            "federation",
            "genesis",
            "loop",
            "metaos",
            "observer",
            "metaos_a",
            "metaos_b",
            "metaos_c",
            "runtime",
            "signal",
            "strategy",
            "validation",
        ],
    ),
)
