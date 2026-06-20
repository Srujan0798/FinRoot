# Observability

What FinRoot exposes so its reasoning is inspectable in dev and demo. (Single-user scope — lightweight.)

## What we observe
- **Reasoning trace** — every pipeline stage (intent → plan → tool calls → synthesis → critique →
  verify) emitted as structured events; rendered live in the UI trace panel.
- **Audit trail** — hash-chained event log (`logs/audit.jsonl`) — the durable, tamper-evident record.
- **Metrics** — `results/metrics.json` (FRB composite, per-axis, baseline delta, latency) — single source.
- **Logs** — structured JSON to stdout (provider, tool, cache hit/miss, rate-limit waits, errors).
- **(Optional) Prometheus** — `/metrics` if the FastAPI surface is enabled (see `prometheus.yml`).

## Key signals
- Reasoning composite score + lift over baseline (the headline).
- Per-tool latency, cache hit rate, failure rate (loud failures, never silent — FM-11).
- Self-Critic pass/refine counts; principles-verifier downgrades ("do not act yet" rate).
- Mock-mode demo latency (must stay < 2s).

## Alert thresholds (dev)
- Any uncited number in a graded run → fail the eval (hard gate).
- Self-Critic accept-rate ≈ 100% with no refinements → likely rubber-stamping → investigate.
- Tool failure rate > 5% in a session → check provider/keys; never substitute synthetic data.

See `INCIDENT_RESPONSE_PLAYBOOK.md` for what to do when a signal trips.
