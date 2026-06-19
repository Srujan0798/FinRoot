# Wave 5 — Self-Critic & Reasoning Layer (the 35% weapon)

**Goal:** the reasoning-quality machinery that separates FinRoot from a tool-caller — the 5-axis
Self-Critic + refinement loop, the Rooted Prudence verifier, self-consistency, and the
explainability/confidence/citation assembly. **Depends on W4. Highest-leverage wave for scoring.**

## Tasks (5)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Self-Critic (5-axis scoring) | reasoning/LLM | `src/finroot/reasoning/critic.py` | W4 |
| 02 | Refinement loop (critique → revise → re-score) | reasoning | `src/finroot/reasoning/refine.py` | 01 |
| 03 | Rooted Prudence Principles verifier | reasoning/domain | `src/finroot/reasoning/principles.py` | W4 |
| 04 | Self-consistency (N candidates → vote) | reasoning | `src/finroot/reasoning/consistency.py` | W4 |
| 05 | Explainability assembly (rationale+risks+confidence+citations) | reasoning | `src/finroot/reasoning/explain.py` | 01,03 |

## Contracts to freeze first
`reasoning.contract.md` — the 5 axes (correctness · risk-awareness · actionability · explainability ·
evidence), score schema + thresholds, refinement stop conditions, the principles checklist, and the
"insufficient evidence → do not act yet" downgrade rule.

## Acceptance
```bash
pytest tests/unit -k "critic or principles or consistency or refine or explain" -v
# critic must FAIL a deliberately bad answer and PASS a good one (class-balanced, §6.9)
pytest tests/golden -k reasoning -v
python -m src.interface.cli --mock "Should I move my entire emergency fund into equity right now?"
# expect: a cautious, risk-first answer (or "do not act yet") — principles verifier engaged
```
The critic must not rubber-stamp — tested against bad answers it MUST catch (HALL_OF_SHAME seed).

## Scoring relevance
**Reasoning Quality (35%) — the single most important wave.** This is the measurable differentiator.
