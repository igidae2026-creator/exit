import sys
from pathlib import Path

IMMUTABLE = {
    "docs/core/METAOS_CONSTITUTION.md",
    "docs/core/METAOS_MASTER_SPEC.md",
}

def norm(p: str) -> str:
    return str(Path(p).as_posix()).lstrip("./")

def check(paths):
    for p in paths:
        if norm(p) in IMMUTABLE:
            print(f"BLOCKED: immutable constitution file modification detected -> {p}")
            sys.exit(1)

if __name__ == "__main__":
    check(sys.argv[1:])
