from __future__ import annotations

import _signal


SIG_DFL = _signal.SIG_DFL
SIG_IGN = _signal.SIG_IGN
default_int_handler = getattr(_signal, "default_int_handler", None)
signal = _signal.signal
getsignal = _signal.getsignal
raise_signal = getattr(_signal, "raise_signal", None)
strsignal = getattr(_signal, "strsignal", None)
pthread_kill = getattr(_signal, "pthread_kill", None)
pidfd_send_signal = getattr(_signal, "pidfd_send_signal", None)
valid_signals = getattr(_signal, "valid_signals", None)

for _name in dir(_signal):
    if _name.startswith("SIG"):
        globals().setdefault(_name, getattr(_signal, _name))

