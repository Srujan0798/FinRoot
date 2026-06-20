# Evals — Financial Reasoning Benchmark (FRB)

> The proof behind FinRoot's 35% Reasoning Quality claim. Eval-driven development per Anthropic
> Jan 2026 "Demystifying evals for AI agents." **This directory holds the eval *specs* and *scaffold*;
> the harness/grader *implementation* is wave-6** (`src/finroot/evaluation/`, `scripts/run_evals.py`).

## Philosophy
A capability is defined by its eval BEFORE the agent can do it. We run tasks across trials, grade
outcomes (not tool-call sequences), compare against baselines, and read transcripts — not just scores.

## Structure
```
evals/
├── tasks/         # FRB task specs (YAML) — what to test (these are written up front)
├── graders/       # grading logic — code_based + llm_judge + human template (impl: wave-6)
├── trials/        # multiple attempts per task (non-determinism)
├── transcripts/   # full records — READ THESE weekly (§6.10)
├── outcomes/      # final states
└── reports/       # pass@k / pass^k summaries → mirrored to results/metrics.json
```

## Metrics
- **pass@k** — success in ≥1 of k attempts (capability).
- **pass^k** — ALL k attempts succeed (production reliability).

| Stage | pass@k | pass^k |
|---|---|---|
| Capability eval | ≥ 50% at k=5 | — |
| Regression suite | ≥ 95% at k=3 | ≥ 80% at k=3 |

## The composite reasoning score (5 axes, 0–1 each)
correctness · risk-awareness · actionability · explainability · evidence-grounding.
FRB compares **baseline RAG → single-agent → full FinRoot**; the headline number is the composite
**lift over RAG** (PRD target ≥ +40%). Single source of truth: `results/metrics.json`.

## Run (after wave-6 ships)
```bash
make evals                         # all tasks, all systems → results/metrics.json + evals/reports/
python scripts/run_evals.py --mock --task 001
```

## Anti-patterns we reject (§6.9)
brittle grading (numeric over-precision / fixed tool sequence) · ambiguous specs · class imbalance
(only "should answer", never "should refuse") · shared state between trials · agent bypasses ·
saturation (100% pass = add harder tasks). When pass^k = 0%, suspect a broken task, not the agent.

## Build workflow
Convert real failures (`HALL_OF_SHAME.md`) + domain questions into 20–50 tasks → run → read
transcripts → calibrate LLM-judge vs human quarterly → promote to regression at pass@5 ≥ 50%.
