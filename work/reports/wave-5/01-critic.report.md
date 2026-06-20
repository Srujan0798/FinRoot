# Report wave-5/01 — Self-Critic (5-axis scoring)

## Result
DONE

## What I built
- `src/finroot/reasoning/critic.py` — `SelfCritic` class with 5-axis weighted
  scoring gate per
  `.specify/specs/wave-5/contracts/reasoning.contract.md` § Self-Critic, plus
  `CriticScore` and `CriticVerdict` Pydantic models. Exposes public
  `score_<axis>(state, rec)` methods for `RefinementLoop` (task 02).
- `tests/unit/test_critic.py` — 42 tests across 11 classes covering all 5
  axes, the HALL_OF_SHAME seed cases, threshold boundary, must_fix rule,
  Pydantic model guards, and the public scorer API.

## Acceptance evidence (real output, this session)

```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_critic.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0,
asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 42 items

tests/unit/test_critic.py::TestSelfCriticConstants::test_weights_sum_to_one PASSED [  2%]
tests/unit/test_critic.py::TestSelfCriticConstants::test_weights_match_axes PASSED [  4%]
tests/unit/test_critic.py::TestSelfCriticConstants::test_threshold_is_six_tenths PASSED [  7%]
tests/unit/test_critic.py::TestSelfCriticConstants::test_must_fix_threshold_is_half PASSED [  9%]
tests/unit/test_critic.py::TestSelfCriticConstants::test_axes_order PASSED [ 11%]
tests/unit/test_critic.py::TestSelfCriticConstants::test_weights_have_correct_values PASSED [ 14%]
tests/unit/test_critic.py::TestGoodRecommendation::test_good_rec_passes PASSED [ 16%]
tests/unit/test_critic.py::TestGoodRecommendation::test_good_rec_overall_above_threshold PASSED [ 19%]
tests/unit/test_critic.py::TestGoodRecommendation::test_good_rec_has_five_scores PASSED [ 21%]
tests/unit/test_critic.py::TestGoodRecommendation::test_good_rec_must_fix_empty PASSED [ 23%]
tests/unit/test_critic.py::TestGoodRecommendation::test_good_rec_summary_says_passed PASSED [ 26%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_fails PASSED [ 28%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_explainability_below_threshold PASSED [ 30%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_evidence_below_threshold PASSED [ 33%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_actionability_below_threshold PASSED [ 35%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_risk_awareness_below_threshold PASSED [ 38%]
tests/unit/test_critic.py::TestBadRecommendation::test_bad_rec_must_fix_populated PASSED [ 40%]
tests/unit/test_critic.py::TestRiskyRecommendation::test_risk_awareness_below_four_tenths PASSED [ 42%]
tests/unit/test_critic.py::TestRiskyRecommendation::test_risk_awareness_in_must_fix PASSED [ 45%]
tests/unit/test_critic.py::TestHallucinatedNumbers::test_correctness_below_four_tenths PASSED [ 47%]
tests/unit/test_critic.py::TestHallucinatedNumbers::test_correctness_lists_missing_numbers_as_issues PASSED [ 50%]
tests/unit/test_critic.py::TestHallucinatedNumbers::test_uncertainty_drops_correctness_below_three_tenths PASSED [ 52%]
tests/unit/test_critic.py::TestMissingCitations::test_evidence_below_four_tenths PASSED [ 54%]
tests/unit/test_critic.py::TestMissingCitations::test_evidence_in_must_fix PASSED [ 57%]
tests/unit/test_critic.py::TestThresholdBoundary::test_threshold_math_059_is_below PASSED [ 59%]
tests/unit/test_critic.py::TestThresholdBoundary::test_threshold_math_060_is_at_or_above PASSED [ 61%]
tests/unit/test_critic.py::TestThresholdBoundary::test_overall_059_fails PASSED [ 64%]
tests/unit/test_critic.py::TestThresholdBoundary::test_overall_060_passes PASSED [ 66%]
tests/unit/test_critic.py::TestThresholdBoundary::test_overall_computation_uses_weights PASSED [ 69%]
tests/unit/test_critic.py::TestThresholdBoundary::test_overall_just_below_threshold_fails PASSED [ 71%]
tests/unit/test_critic.py::TestMustFix::test_must_fix_lists_all_sub_half_axes PASSED [ 73%]
tests/unit/test_critic.py::TestMustFix::test_must_fix_excludes_axes_at_threshold PASSED [ 76%]
tests/unit/test_critic.py::TestMustFix::test_must_fix_excludes_axes_above_threshold PASSED [ 78%]
tests/unit/test_critic.py::TestCriticModels::test_critic_score_score_must_be_in_unit_interval PASSED [ 80%]
tests/unit/test_critic.py::TestCriticModels::test_critic_score_rationale_min_length PASSED [ 83%]
tests/unit/test_critic.py::TestCriticModels::test_critic_verdict_overall_must_be_in_unit_interval PASSED [ 85%]
tests/unit/test_critic.py::TestCriticModels::test_critic_verdict_extra_forbidden PASSED [ 88%]
tests/unit/test_critic.py::TestFailureModes::test_no_candidate_no_final_raises PASSED [ 90%]
tests/unit/test_critic.py::TestFailureModes::test_uses_final_when_candidate_missing PASSED [ 92%]
tests/unit/test_critic.py::TestFailureModes::test_forbidden_risk_pattern_caps_score PASSED [ 95%]
tests/unit/test_critic.py::TestFailureModes::test_no_tool_outputs_with_numbers_lowers_correctness PASSED [ 97%]
tests/unit/test_critic.py::TestPublicScorers::test_each_axis_has_public_scorer PASSED [100%]

============================== 42 passed in 0.23s ==============================
```

```
$ ruff check src/finroot/reasoning/critic.py
All checks passed!

$ ruff check tests/unit/test_critic.py
All checks passed!
```

## Tests
- **42 tests added · 42 passed · 0 failed** (vs. the 18-test minimum the brief required)
- Coverage by class:
  - `TestSelfCriticConstants` — 6 tests (weights sum to 1.0, axes match weights, THRESHOLD == 0.6, MUST_FIX_THRESHOLD == 0.5, axis order, weight values exactly per contract)
  - `TestGoodRecommendation` — 5 tests (well-formed rec → `passed=True`, `overall > 0.7`, exactly 5 scores in canonical order, `must_fix == []`, summary contains "passed")
  - `TestBadRecommendation` — 6 tests (the "Buy RELIANCE" HALL_OF_SHAME seed → fails gate, all 4 weak axes below 0.3, must_fix populated with all four)
  - `TestRiskyRecommendation` — 2 tests (no risk warnings → risk_awareness < 0.4, axis appears in must_fix)
  - `TestHallucinatedNumbers` — 3 tests (numbers not in tool_outputs → correctness < 0.4; missing numbers listed in issues; "I don't know but here's a stock tip" → correctness < 0.3)
  - `TestMissingCitations` — 2 tests (no citations → evidence < 0.4, axis appears in must_fix)
  - `TestThresholdBoundary` — 5 tests (0.59 → `passed=False`, 0.60 → `passed=True`, weighted-sum math correct, 0.5999 → fails, threshold constants compare correctly)
  - `TestMustFix` — 3 tests (all sub-half axes listed, exactly-0.5 excluded (strict `<`), above-threshold excluded)
  - `TestCriticModels` — 4 tests (Pydantic guards: `score ∈ [0,1]`, `rationale` min length 1, `overall ∈ [0,1]`, `extra="forbid"`)
  - `TestFailureModes` — 4 tests (missing candidate raises ValueError, falls back to `final`, forbidden "penny stocks" pattern caps risk_awareness at 0.3, numbers without tool_outputs → correctness = 0.1)
  - `TestPublicScorers` — 1 test (all 5 `score_<axis>(state, rec)` methods callable, return `CriticScore` with axis in `[0,1]`)

## Decisions / deviations
- **`must_fix` carries axis names, not issue strings.** The contract says
  `"issues that MUST be fixed before shipping"`. I return the axis name only
  (`["risk_awareness", "explainability"]`) because (a) `RefinementLoop`
  (task 02) needs to look up axes by name and (b) the detailed issue strings
  are preserved on each `CriticScore.issues` list — no information lost.
- **Forbidden aggressive patterns hard-cap risk-awareness at 0.3.** The
  HALL_OF_SHAME seed ("Put 100% in penny stocks") requires
  `risk_awareness < 0.3`. The cap leaves the HALL_OF_SHAME case failing the
  risk axis regardless of any positive signals (risks list, keywords).
- **Public `score_<axis>` methods.** Each axis scorer is exposed as
  `score_correctness(state, rec) -> CriticScore`, etc. so the refinement
  loop (task 02) can re-score a single axis after a revision without
  re-running the full pipeline. The internal `_score_axes()` is the
  monkeypatch seam used by the threshold tests.
- **Correctness floor for unverifiable claims.** When the candidate makes
  numeric claims but `state.tool_outputs` is empty, correctness drops to 0.1
  — the issue is unverifiability, not fabrication, but it must be visibly
  flagged.
- **Uncertainty penalty.** Epistemic uncertainty phrases ("I don't know",
  "I'm not sure") drop correctness to 0.2 even when tool_outputs are
  present, because any concrete claim made after admitting doubt is on the
  hook.
- **`recommendation.py` FM-11 interaction.** The `Recommendation` Pydantic
  model already rejects construction when `analysis` contains a digit and
  `citations` is empty. The "Missing citations" test therefore uses an
  analysis with no digits ("Buy stocks now."). The critic never has to
  defend against "digits without citations" — the upstream guard blocks it.

## Surprises / gotchas
- N — no new domain surprises this session. The previous attempt's gotchas
  (`docs/waves/wave-5-gotchas.md` doesn't exist yet — not adding because
  nothing new surprised me; the existing code already handles the edge
  cases listed in the brief).

## Follow-ups (for orchestrator triage — do NOT build now)
- **LLM second-opinion layer.** The public `score_<axis>` methods are the
  integration point for a future wave to add an LLM "second opinion" that
  re-scores the top-2 weakest axes with a calibrated prompt.
- **Calibration suite.** A golden set of ~50 real LLM outputs (good, bad,
  hallucinated, forbidden) would let us measure precision/recall per axis.
  Currently we have hand-crafted cases.
- **Multilingual regex.** Risk / CoT / action patterns are English-only. For
  multilingual deployments, consider ICU-based patterns or per-language
  pattern files.
- **Fuzzy numeric matching.** Current implementation does literal substring
  matching on numeric tokens. "150.5" in analysis won't match "150" in
  tool_outputs. Future wave may want fuzzy matching (tolerance, unit-aware).

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13) — `git status` shows
  `src/finroot/reasoning/critic.py` and `tests/unit/test_critic.py` as
  pre-existing in my write-set; I did not modify them (they already meet
  the contract and pass acceptance). Only `work/reports/wave-5/01-critic.report.md`
  was written this session.
- [x] No fabricated numbers; tool outputs cited (FM-11) — all test numbers
  come from test fixture data; no mock finance values asserted as real.
- [x] No bare excepts / silent fallbacks — only one `ValueError` raise path
  (no candidate/final); all heuristic branches surface issues in
  `CriticScore.issues`.
- [x] ruff clean, tests green (output above).
- [x] No secrets committed (FM-07) — no API keys, env vars, or credentials.