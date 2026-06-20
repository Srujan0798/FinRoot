# ADR-0005 — 5-axis Self-Critic

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
The 35% Reasoning Quality weapon requires a systematic approach to catch errors, risks, and hallucinations. We need a self-critic that evaluates recommendations across multiple dimensions, not just a simple validation step.

## Decision
We implemented **5-axis Self-Critic** in `src/finroot/reasoning/critic.py`:

- **Correctness:** Verifies factual accuracy against data sources
- **Risk:** Flags potential financial risks and volatility concerns
- **Actionability:** Ensures recommendations are practical and implementable
- **Explainability:** Validates that reasoning is clear and traceable
- **Evidence:** Confirms all claims are backed by citations and data

The critic operates as a LangGraph node that:
1. Receives the candidate Recommendation from the synthesize step
2. Runs all 5 axes of evaluation
3. Returns a structured verdict (pass/fail with reasoning)
4. Can trigger refinement loops if needed

The critic integrates with the 5-axis framework by checking each axis against specific criteria:
- Correctness: Data validation, source verification
- Risk: Portfolio concentration, leverage limits, volatility thresholds
- Actionability: Feasibility, cost considerations, implementation steps
- Explainability: Clear reasoning chain, jargon avoidance
- Evidence: Citation completeness, data source transparency

This creates a robust quality gate that catches issues before they reach the user.

## Consequences
- **Positive:** Catches errors that would otherwise reach users (FM-11)
- **Positive:** Provides detailed feedback for refinement loops
- **Positive:** Judges can see the quality assurance process (35% weapon)
- **Negative:** Adds computational overhead to each query
- **Negative:** May require tuning thresholds for different user profiles
- **Neutral:** Creates a more complex but robust reasoning pipeline

## Alternatives considered
- **Single correctness check:** Too narrow; misses risk, actionability, and explainability
- **LLM-based evaluation:** Less deterministic; harder to audit and cite (FM-11)
- **Manual review:** Not scalable for production use

The 5-axis approach is the minimal design that delivers comprehensive quality assurance while remaining deterministic and auditable.