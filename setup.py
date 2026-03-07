from setuptools import find_packages, setup

RUNTIME_PACKAGES = [
    "app*",
    "artifact*",
    "core*",
    "domains*",
    "ecosystem*",
    "evolution*",
    "federation*",
    "genesis*",
    "kernel*",
    "loop*",
    "metaos*",
    "metaos_a*",
    "metaos_b*",
    "metaos_c*",
    "observer*",
    "runtime*",
    "signal*",
    "strategy*",
    "validation*",
]

setup(
    name="metaos",
    version="0.4.0rc1",
    include_package_data=True,
    package_data={"validation": ["ownership_manifest.json"]},
    packages=find_packages(where=".", include=RUNTIME_PACKAGES),
)
