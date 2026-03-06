from setuptools import find_packages, setup

setup(
    name="metaos",
    version="0.1.0",
    packages=find_packages(
        include=["metaos*", "kernel*", "insights*", "metrics*", "strategy*", "src*"]
    ),
)
