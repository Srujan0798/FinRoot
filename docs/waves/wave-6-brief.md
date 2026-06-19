# Wave 6 — Evaluation Harness (FRB: prove the 35%)

**Goal:** the Financial Reasoning Benchmark that *proves* FinRoot beats a baseline — the evidence
behind the 35% claim. **Depends on W4 + W5.** Without this, reasoning quality is just a claim.

## Tasks (5)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | FRB question bank (domain-spread, class-balanced) | domain/data | `evals/tasks/**`, `data/gold/frb_questions.json` | W5 |
| 02 | Graders: code-based + LLM-judge + human template | eval eng | `evals/graders/code_based.py`, `evals/graders/llm_judge.py`, `evals/graders/human_review_template.md` | 01 |
| 03 | Baselines (RAG + single-agent) for comparison | ML | `src/finroot/evaluation/baselines.py` | W4 |
| 04 | Harness runner (pass@k / pass^k, trials) | eval eng | `src/finroot/evaluation/harness.py`, `scripts/run_evals.py` | 01,02,03 |
| 05 | Report generator → metrics.json + delta | eval eng | `src/finroot/evaluation/report.py`, `evals/reports/.gitkeep` | 04 |

## Contracts to freeze first
`evals.contract.md` — task YAML shape (per §4.23), grader interface, metric definitions (pass@k,
pass^k), the single metrics source (`results/metrics.json`), and the anti-patterns to reject (§6.9).

## Acceptance
```bash
make evals                              # runs FRB; writes results/metrics.json + evals/reports/*
python scripts/run_evals.py --mock --task 001   # single task end-to-end
pytest tests/unit -k eval -v
```
Output proves the composite lift target (PRD §8: ≥ +40% vs RAG). Numbers live ONLY in
`results/metrics.json`; docs reference it (FM-05/12). Read transcripts, not just scores (§6.10).

## Scoring relevance
**Reasoning Quality (35%) — the proof.** Turns "we reason well" into a measured, reproducible delta.
