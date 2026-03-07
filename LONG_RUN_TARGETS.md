# Long-Run Targets

- `smoke`: >= 256 ticks, profile target 1,000 ticks, >= 4 surviving lineages, >= 3 active domains
- `bootstrap`: >= 1,000 ticks, >= 4 surviving lineages, >= 3 active domains
- `aggressive`: >= 5,000 ticks, >= 6 surviving lineages, >= 4 active domains
- `soak`: >= 50,000 ticks, >= 8 surviving lineages, >= 4 active domains
- `production`: unbounded runtime by default; long-run validation target >= 100,000 ticks when explicitly checked

Target quality floors:

- effective lineage diversity >= 0.55
- preferred dominance ceiling <= 0.35
- hard intervention threshold <= 0.50
- stability score >= 0.70
- economy balance score >= 0.65
- replay mismatches = 0
- append-only violations = 0
- budget cycle count must be nontrivial
- knowledge density and memory growth must remain positive in meaningful runs
