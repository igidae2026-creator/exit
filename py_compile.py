from __future__ import annotations

import argparse
import builtins
import compileall
import sys
from pathlib import Path


class PyCompileError(Exception):
    pass


def compile(
    file: str,
    cfile: str | None = None,
    dfile: str | None = None,
    doraise: bool = False,
    optimize: int = -1,
    invalidation_mode: object | None = None,
    quiet: int = 0,
) -> str | None:
    del cfile, dfile, optimize, invalidation_mode, quiet
    try:
        source = Path(file).read_text(encoding="utf-8")
        builtins.compile(source, file, "exec")
        return file
    except Exception as exc:
        error = PyCompileError(str(exc))
        if doraise:
            raise error from exc
        return None


def _compile_target(target: str) -> bool:
    path = Path(target)
    if path.is_dir():
        return compileall.compile_dir(str(path), quiet=1, force=False)
    if path.is_file():
        return compileall.compile_file(str(path), quiet=1, force=False)
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="py_compile")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    ok = True
    for target in args.paths:
        ok = _compile_target(target) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
