import importlib
import os


def load_domains():
    domains = []
    for f in os.listdir("domains"):
        if f.endswith(".py"):
            name = f[:-3]
            domains.append(importlib.import_module(f"domains.{name}"))
    return domains
