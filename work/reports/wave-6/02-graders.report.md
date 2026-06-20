# Report wave-6/02 — Graders (code-based + LLM-judge + human template)

## Result
DONE

## What I built
- `evals/graders/__init__.py` — package surface; re-exports `GradeResult`, `grade_code`, `grade_llm`, `JUDGE_AXES`, `build_judge_prompt`.
- `evals/graders/code_based.py` — deterministic grader: Pydantic `GradeResult`, `grade_code(task, state)` keyword + red-flag + citation + numeric + confidence checks, weighted score (sum-to-1.0), hard-pass formula from the contract.
- `evals/graders/llm_judge.py` — 5-axis LLM rubric grader: `grade_llm(task, state, judge_llm)`, prompt builder, regex parser, deterministic heuristic fallback so `MockProvider` is test-stable.
- `evals/graders/human_review_template.md` — weekly reviewer form covering the 5 axes, honesty checks (fabrication, guaranteed-returns, adversarial-trap handling), verdict (PASS / REVISE / FAIL), and sign-off.
- `tests/unit/test_graders.py` — 28 tests (≥12 required) covering every contract criterion + the anti-patterns.

> The two pre-existing scaffolds at `evals/graders/{code_based,llm_judge}.py` were placeholder `NotImplementedError` stubs that OS-setup left for wave-6 to replace. I rewrote both files in full, so the graders directory now contains working implementations consistent with the wave-6 contract.

## Acceptance evidence (real output, this session)

```
$ cd /Users/srujansai/Desktop/FinRoot && PYTHONPATH=src python3 -m pytest tests/unit/test_graders.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.0, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_loop_scope=function, asyncio_default_test_loop_scope=function
collected 28 items

tests/unit/test_graders.py ............................                  [100%]

============================== 28 passed in 0.15s ==============================
exit: 0
```

```
$ cd /Users/srujansai/Desktop/FinRoot && ruff check evals/graders/ tests/unit/test_graders.py
All checks passed!
exit: 0
```

Sanity sweep — neighboring tests untouched, no regressions:

```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_critic.py tests/unit/test_baselines.py tests/unit/test_frb_bank.py tests/unit/test_graders.py
........................................................................ [ 59%]
..................................................                       [100%]
122 passed in 0.18s
```

## Tests
- 28 unit tests in `tests/unit/test_graders.py` (contract required ≥ 12).
- Coverage map (test class → contract criterion):
  - `TestCodeBased` (12 tests)
    - passes-good-answer, fails-on-must-not-hit, fails-on-zero-citations,
      numeric-match-within-tolerance, numeric-mismatch-fails, numeric-zero-extracted-fails,
      confidence-mismatch-fails, must-mention-keyword-coverage, garbage-answer-fails,
      state-without-final-raises, score-uses-expected-weights, handles-currency-format-with-indian-separators.
  - `TestLLMJudge` (8 tests)
    - returns-GradeResult-with-breakdown, deterministic-in-mock, axes-dict-has-all-five,
      garbage-answer-fails-judge, state-without-final-raises, judge-none-raises,
      judge-prompt-contains-axes-and-keywords, evidence-alias-maps-to-evidence-grounding.
  - `TestNoRubberStamp` (2 tests) — verifies good vs junk vs red-flag answers spread to distinct outcomes in both graders (the anti-pattern guard).
  - `TestGradeResultContract` (3 tests) — required fields, `extra="forbid"`, score normalization.
  - `TestHumanReviewTemplate` (3 tests) — all 5 axes listed, honesty checks present, verdict section present.
- All 28 tests pass; ruff clean on `evals/graders/` and the test file.

## Decisions / deviations
1. **Weighted-score weights** (`WEIGHTS` in `code_based.py`): `{must_mention: 0.30, citation_count: 0.40, confidence: 0.10, actionability_proxy: 0.15, length_proxy: 0.05}` (sum to 1.0). Chosen so that *missing citations alone* (the FM-11 anti-pattern) drops a perfect answer from 1.00 → 0.60, on the threshold boundary, and *combined with any other deficiency* fails clearly. The brief said "passed = score >= 0.6 AND no must_not hit AND numeric matches (if required)" — I added `min_citations > 0 ⇒ citations_passed is required` as a structural enforcement of the contract's anti-pattern ("answer with zero citations on a numeric claim → must FAIL"). Documented in the `WEIGHTS` docstring and the `citations` block of the breakdown.
2. **Citation count falls back to `state.tool_outputs`** when `state.final.citations` is empty — supports baselines (task 03) that produce a raw `AgentState` without populating the user-facing `Recommendation.citations`. Brief said "count `state.final.citations` (or tool_outputs) ≥ `min_citations`".
3. **Numeric extraction**: two-pass regex — currency-prefixed tokens (`₹`, `Rs.`, `INR`, `$`, `€`, `£`) preferred over plain numbers; among candidates, the **closest match** to `expected.numeric_answer` wins. This is deterministic, audit-friendly, and avoids the agent picking the wrong number when the answer discusses both a holding and a tax (e.g., "₹1,00,000 gain → ₹10,400 tax"). Indian-lakh notation (`1,00,000`) is parsed correctly (covered by `test_handles_currency_format_with_indian_separators`).
4. **`GradeResult` Pydantic model** lives in `code_based.py` (the contract calls for a single shared type); re-exported from `evals/graders/__init__.py`. `grader: str` defaults to `"code"`; `llm_judge.py` overrides it. `extra="forbid"` is enforced (covered by `test_extra_forbid_on_grade_result`).
5. **LLM-judge axis names**: the LLM-judge uses the longer `evidence_grounding` name while the critic uses `evidence`. The judge *accepts either* via regex aliasing, so an upstream critic-style response parses correctly. Covered by `test_evidence_alias_maps_to_evidence_grounding`.
6. **`JUDGE_AXES` resolution**: imported from `finroot.reasoning.critic` if available (per the brief's "reuses the critic's axes if importable"), otherwise falls back to a hard-coded 5-tuple — degrade gracefully. The critic's axes are mapped: `evidence → evidence_grounding`.
7. **MockProvider determinism**: `MockProvider` returns canned prose that doesn't follow the rubric. The LLM-judge's regex parser finds nothing → `score_source = "heuristic_fallback"`, which produces a deterministic, content-based 5-axis score. So `MockProvider` is test-stable (covered by `test_deterministic_in_mock`).
8. **No rubber-stamp**: the spread tests (`TestNoRubberStamp`) explicitly construct three answers (good / junk / red-flag) and assert the grader produces three distinct outcomes — not three blanks or three passes.

## Surprises / gotchas
- The `evals/` directory is at the repo root, **not** under `src/`, and has no `__init__.py`. With `PYTHONPATH=src` (the orchestrator's acceptance command), `evals.graders` is not importable as a regular package. Solution in `tests/unit/test_graders.py`: prepend the repo root to `sys.path` at module top — `evals` becomes a PEP 420 namespace package, `evals/graders/__init__.py` (which I wrote) makes `evals.graders` resolvable. No other file in my Writes set needs this. **Added to `docs/waves/wave-6-gotchas.md`.**
- The pre-existing `evals/graders/{code_based,llm_judge}.py` and `human_review_template.md` were **placeholder `NotImplementedError` stubs** left by OS-setup. They are in my Writes set, so rewriting them is in scope — confirmed via the file map in `evals.contract.md` § File map (W6-02 owns exactly these files).

## Follow-ups (for orchestrator triage — do NOT build now)
- The contract spec'd `evidence_grounding`; the existing critic uses `evidence`. A future wave could unify the naming across the critic + the LLM-judge prompt template + the human-review form so downstream aggregators don't need the alias. BACKLOG.
- A future wave may want to **tune the weights** based on human-review agreement (per §6.10). The current weights are a defensible default but the `WEIGHTS` constant is exposed in the breakdown for easy A/B. BACKLOG.
- The LLM-judge's heuristic fallback is intentionally simple (5 keyword families + presence checks). A future wave could replace it with a richer rule-based scorer (e.g., borrow regexes from `finroot.reasoning.critic`). BACKLOG.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13). Verified with `git status` — only the 5 Writes files appear modified or new.
- [x] No fabricated numbers; tool outputs cited (FM-11). All test answers and task specs use either the canonical `data/gold/frb_questions.json` numbers (frb-001, frb-012) or synthetic numbers clearly labeled (e.g., test input `₹99,999` is the deliberately-wrong value used to verify the mismatch branch).
- [x] No bare excepts / silent fallbacks. `grade_code` and `grade_llm` raise `ValueError` on `state.final is None` and `judge_llm is None`; the LLM-judge's "fallback" is deterministic and records its `score_source` in the breakdown for auditability.
- [x] ruff clean, tests green (output above).
- [x] No secrets committed (FM-07). No API keys, no env reads, no network.
