# ADR-0006 — Sovereign-first / Mock default

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
The PS requires a sovereign, reasoning-first AI that doesn't rely on closed APIs. We need to:

1. Prefer local models (Ollama) for privacy and sovereignty
2. Have a Mock fallback for judging and offline use
3. Support cloud providers as optional accelerators
4. Never have a closed API on the critical path

This is the privacy/sovereignty story (Idea 15%) that judges look for.

## Decision
We implemented **Sovereign-first / Mock default** in:

- `src/finroot/llm/base.py` — abstract LLM provider interface
- `src/finroot/llm/ollama.py` — local Ollama provider (default)
- `src/finroot/llm/mock.py` — deterministic Mock provider for judging
- `src/finroot/llm/groq.py` — Groq cloud provider (optional)
- `src/finroot/llm/openai.py` — OpenAI cloud provider (optional)

The system uses **Mock mode by default** (no API keys required) for:
- Judge safety (offline, reproducible)
- Demo reliability (no network dependencies)
- Sovereign operation (no data leaving the machine)

Cloud providers are lazy-loaded and only used if explicitly configured via environment variables.

This design ensures:
- **FM-07:** No secrets in production; samples are synthetic
- **FM-11:** Mock provides deterministic, auditable outputs
- **FM-01:** No state drift; same inputs always produce same outputs in Mock mode

## Consequences
- **Positive:** Judges can run without API keys; reproducible results
- **Positive:** Sovereign operation; no data leaves the machine unless explicitly opted-in
- **Positive:** Privacy-first by design; users control their data
- **Negative:** Local model performance may be slower than cloud
- **Negative:** Requires local model installation for optimal performance
- **Neutral:** Adds complexity to provider management but improves sovereignty

## Alternatives considered
- **Cloud-first:** Would compromise sovereignty and require API keys
- **No Mock:** Would make judging harder and less reproducible
- **Hardcoded provider:** Would violate FM-07 (secrets) and FM-11 (no silent failures)

The Sovereign-first approach is the minimal design that delivers privacy, sovereignty, and judge safety while maintaining flexibility for optional cloud acceleration.