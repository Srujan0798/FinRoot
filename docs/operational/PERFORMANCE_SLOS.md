# Performance SLOs

> Targets that keep the demo snappy and the agent usable. Enforced in `tests/performance/` (wave-6+).
> Numbers measured into `results/metrics.json`, never hand-typed (FM-05).

| Operation | Target P95 | Acceptable P95 | Minimum P95 |
|---|---|---|---|
| Mock-mode query (full pipeline, judge path) | 1.0s | 2.0s | 3.0s |
| Ollama-mode query (llama3.1:8b, local) | 8s | 20s | 40s |
| Single tool call (cached) | 5ms | 20ms | 50ms |
| Single tool call (cold, keyless source) | 300ms | 1s | 3s |
| FRB single-task grade (code-based) | 50ms | 150ms | 400ms |
| UI first paint (Streamlit) | 1.5s | 3s | 5s |

## Enforcement
- `tests/performance/` runs the Mock path and asserts the judge-path P95 < Minimum (CI gate).
- A perf regression workflow (`perf_regression.yml`, T2) compares against the last shipped wave.

## Notes
- The **Mock path is the SLO that matters for judging** — it must be fast and deterministic.
- Local-model latency is a sovereignty trade-off, surfaced honestly (FRB measures quality vs speed).
