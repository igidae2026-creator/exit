from __future__ import annotations

from typing import Sequence


def build_parser():
    from metaos.cli import build_parser as _build_parser

    return _build_parser()


def main(argv: Sequence[str] | None = None) -> int:
    from metaos.cli import main as _main

    return _main(argv)


__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
