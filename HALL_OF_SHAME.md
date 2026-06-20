# Hall of Shame — Failure Pattern Archive

> Records failure patterns so they are never repeated. **Learning tool, not blame tool.**
> A worker who hits a similar bug greps here first. The `self-evolve` skill scans this before
> dispatching new tasks. Every CRITICAL bug → entry here + regression test + eval task + prevention rule.

## Format
```
## Pattern N: <descriptive title>
- Date · Test/Component · Severity (Critical|High|Medium|Low)
- Root cause: what actually went wrong
- Impact: what broke / what slipped past tests
- Fix: file + line refs + commit hash
- Prevention: new test / lint rule / convention / ADR that stops recurrence
```

---

## Seeded domain-specific anti-patterns to guard from day one
> These are *expected* finance-agent failure modes pre-loaded from the design phase so workers
> avoid them before they happen. Promote to a numbered Pattern with a commit hash if one recurs.

- **Hallucinated financial figures.** LLM invents a P/E, price, or tax rate instead of calling a
  tool. → Prevention: every numeric claim must cite a tool output; FRB grader rejects uncited
  numbers; `RiskCalculationTool`/`MarketDataTool` are the only number sources (FM-11).
- **Silent tool fallback to stale cache.** Tool fails, returns cached data without flagging it. →
  Prevention: cache hits are labeled with age; expired data fails loud or is marked low-confidence.
- **Overconfident advice on thin evidence.** Agent gives "buy/sell" with one data point. →
  Prevention: Rooted Prudence verifier blocks action recommendations below an evidence threshold;
  "insufficient evidence → do not act yet" is a valid (and tested) output.
- **Self-Critic rubber-stamping.** Critic always returns high scores (no signal). → Prevention:
  eval class-balance includes deliberately bad answers the critic MUST catch (eval anti-pattern §6.9).
- **Tax engine drift.** Hardcoded slabs go stale or contradict between tools. → Prevention: tax
  rules live in ONE source (`data/tax_rules.json`), asserted at load; deterministic, unit-tested.
- **Eval bypass.** Agent "passes" FRB by pattern-matching the question instead of reasoning. →
  Prevention: held-out paraphrase set; transcript review weekly (§6.10).

## Numbered patterns (added as real failures occur)
*(none yet — fill during the build)*
