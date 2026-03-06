"""Deprecated compatibility shim. Canonical owner: runtime.oed_orchestrator"""

import sys

import runtime.oed_orchestrator as _canonical

sys.modules[__name__] = _canonical
