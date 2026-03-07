from metaos.runtime.soak_runner import run_soak

ticks, summary = run_soak(ticks=256, seed=11, fail_open=True)
print(ticks[-1] if ticks else {})
print(summary)
