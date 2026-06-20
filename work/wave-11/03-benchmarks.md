# Task wave-11/03 — Performance Benchmarks + Load Testing

> Read `work/WORKER_PROMPT.md` then build. Shows scalability.

## Objective
Add performance benchmarks that measure pipeline latency, throughput, and memory usage.
This shows judges the system is production-ready.

## Writes (ONLY these)
- `tests/performance/test_benchmarks.py`
- `tests/performance/__init__.py`
- `scripts/run_benchmarks.py`

## Forbid
`src/**` (import only), `evals/**`, `data/gold/**`.

## Steps
1. `tests/performance/test_benchmarks.py` (8+ tests):
   - Measure answer() latency in mock mode (target: < 5s)
   - Measure concurrent answer() calls (target: 10 parallel)
   - Measure memory usage during pipeline execution
   - Measure tool execution time
   - Measure synthesis time
   - Measure critic evaluation time
   - Measure full pipeline end-to-end time
   - Measure FRB harness execution time
2. `scripts/run_benchmarks.py`:
   - Run all benchmarks and output results to JSON
   - Include system info (Python version, OS, etc.)
   - Output format: `{"benchmarks": [...], "system": {...}, "timestamp": "..."}`
3. Use `time.perf_counter()` for timing, `tracemalloc` for memory.
4. Use `@pytest.mark.performance` marker.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/performance/ -v -m performance
PYTHONPATH=src python3 scripts/run_benchmarks.py
ruff check tests/performance/ scripts/run_benchmarks.py
```

## Report
`work/reports/wave-11/03-benchmarks.report.md`
