# FinRoot — Executive Summary

> Sovereign, Reasoning-First AI Financial Agent
> Commit: `ee438ae`

---

## What It Is

FinRoot is a multi-agent AI financial reasoning system built on LangChain + LangGraph. It is not a chatbot wrapper — it is a reasoning pipeline that decomposes financial queries, dispatches them to specialist agents (Portfolio, Risk, Market, News, Tax), self-critiques the output on five quality axes, and returns cited, risk-aware, confidence-labeled answers with a tamper-evident audit trail.

The system runs sovereign-first: local inference via Ollama by default, with cloud providers (OpenAI, Groq) as optional fallbacks. User financial data never leaves the machine unless explicitly configured otherwise.

---

## Why It Matters

**The Problem:** Individual investors and small family offices face a structural disadvantage. Institutional players have research teams, risk models, compliance infrastructure, and audit trails. Retail investors get chatbots that hallucinate stock picks with no reasoning transparency.

**The Gap:** Existing AI finance tools are prompt wrappers — no reasoning trace, no self-critique, no risk flags, no audit. When they're wrong, the user has no way to understand why. Regulatory frameworks (MiFID II, SEC guidance) increasingly demand explainability that these tools cannot provide.

**The Consequence:** Users either trust blindly (risk) or don't trust at all (no adoption). Neither is acceptable for financial decision-making.

---

## The Measured Edge

FinRoot includes a Financial Reasoning Benchmark (FRB) — a curated set of financial queries scored by human judges across five axes: Accuracy, Completeness, Risk Awareness, Evidence Quality, and Actionability.

A 5-axis self-critic evaluates every answer before it reaches the user, catching unsupported claims, missing risk flags, and incomplete evidence. A principles verifier enforces financial reasoning standards (no unhedged recommendations, confidence labels required, evidence or silence).

**FRB results (measured):** FinRoot's full reasoning pipeline scores **mean 0.795** across 83 financial
reasoning tasks spanning 11 domains, vs **0.334** for a naive RAG baseline — a **+137.8% composite lift**,
on pass@1 **0.193 vs 0.289** for RAG. All numbers from `results/metrics.json` at `as_of_sha = 8d4d03f`,
regenerable in ~63s with `make evals`.

This is not a claim — it is a measurement with a reproducible harness.

---

## The Moat

Three defensible advantages:

1. **Digital Twin:** A persistent financial profile that learns the user's risk tolerance, investment goals, tax situation, and portfolio over time. Every answer is personalized — not generic. This compounds with use.

2. **Sovereignty:** Local-first architecture means no vendor lock-in, no data exfiltration, no API dependency. The system works offline (Mock mode). Cloud providers are optional, not required.

3. **Audit Trail:** Every reasoning step, tool call, critic evaluation, and final answer is hash-chained into a tamper-evident log. Not just logging — provable integrity. Users (and regulators) can verify exactly how any answer was produced.

---

## The Ask

FinRoot is built for SCALE ML Club PS-1 ("Build an AI Agent for Finance"). The system is complete: 6 agents, 12 tools, 4-tier memory, 5-axis critic, FRB benchmark, Docker deployment, Streamlit UI, Typer CLI, and a reproducible demo harness.

We are looking for evaluation across all four scoring axes — and we built to win every one.
