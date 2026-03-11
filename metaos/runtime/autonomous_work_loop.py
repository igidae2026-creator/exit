"""Deprecated compatibility shim. Canonical owner: runtime.autonomous_work_loop"""

import sys

import runtime.autonomous_work_loop as _canonical

sys.modules[__name__] = _canonical
