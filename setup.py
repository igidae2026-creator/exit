from setuptools import find_packages, setup

setup(
    name="metaos",
    version="0.4.0rc1",
    packages=find_packages(
        where=".",
        include=[
            "app",
            "artifact",
            "domains",
            "genesis",
            "metaos",
            "metaos_a",
            "metaos_b",
            "metaos_c",
            "runtime",
            "validation",
        ],
    ),
)
