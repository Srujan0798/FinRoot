# Report wave-2/04 — Memory Manager (Unified Facade)

## Result
DONE

## What I built
- `src/finroot/memory/manager.py` — `MemoryManager` unified facade + `create()` factory. Composes `WorkingMemory` + `SemanticMemory` + `DigitalTwinStore` into a single object that wave-4 agents can use without touching the underlying stores. Auto-remember threshold (>50 chars), partial twin updates with re-validation, reserved-field protection, fail-loud on missing twins.
- `tests/unit/test_memory_manager.py` — 45 tests across 6 classes (`TestConstruction`, `TestAddTurnAndAutoRemember`, `TestRememberAndRecall`, `TestGetAndUpdateTwin`, `TestCreateFactory`, `TestMockDelegation`) plus one direct schema check. Covers construction validation, every delegation, the 50-char auto-remember boundary, partial update, persistence, reserved-field rejection, factory wiring, and mock-based delegation sanity.
- `tests/integration/test_memory_integration.py` — 5 integration tests using `tmp_path` for isolated on-disk workspaces. The headline test does the full round-trip the brief requires: create manager → 5 turns (mixed short/long) → recall relevant → save twin → reload manager → twin persists, semantic history persists, working is fresh.

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_memory_manager.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pytest.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 45 items

tests/unit/test_memory_manager.py ...................................... [ 84%]
.......                                                                  [100%]

============================== 45 passed in 2.66s ===============================

$ PYTHONPATH=src python3 -m pytest tests/integration/test_memory_integration.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pytest.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 5 items

tests/integration/test_memory_integration.py .....                       [100%]

============================== 5 passed in 1.70s ===============================

$ ruff check src/finroot/memory/manager.py
All checks passed!
```

## Tests
- **45 unit tests** added · 45/45 pass (2.66s) · no coverage data collected
  - `TestConstruction` (6): basic wiring, rejects non-`WorkingMemory` / non-`SemanticMemory` / non-`DigitalTwinStore` / empty / non-string `user_id`
  - `TestAddTurnAndAutoRemember` (9): delegation, short turn not remembered, empty not remembered, exact 50 chars NOT remembered (boundary), 51 chars IS remembered with `user_id`/`role`/`source` metadata, role/content validation, `get_context` returns fresh list
  - `TestRememberAndRecall` (9): returns doc_id, `metadata=None` treated as empty, caller metadata preserved (plus auto-injected `user_id`), non-string `text` rejected, delegation to `semantic.search`, default `k=5`, empty store returns `[]`, `k` validation, query type validation
  - `TestGetAndUpdateTwin` (9): loads, missing raises `KeyError`, partial update preserves untouched fields, persists across reload, missing twin on update raises, `user_id` change rejected as reserved, unknown field raises `ValidationError`, out-of-range `age` raises `ValidationError`, `updated_at` advances
  - `TestCreateFactory` (4): default paths return valid manager, custom paths wired, `max_turns` propagates, persistence across instances
  - `TestMockDelegation` (7): white-box proof of delegation with `MagicMock(spec=...)` — working.add, semantic.add (with `user_id` injection), working.get_messages, semantic.search, twin_store.load, the load→copy→save order in update_twin
  - Schema check (1): `sqlite_master` contains the `digital_twins` table
- **5 integration tests** added · 5/5 pass (1.70s)
  - `test_full_round_trip_add_recall_persist_reload`: the full end-to-end the brief specifies (5 turns, recall, save twin, reload, twin persists)
  - `test_fresh_user_get_twin_raises_across_managers`: `KeyError` is consistent across instances
  - `test_different_users_have_independent_twins`: alice and bob on the same store don't cross-contaminate
  - `test_semantic_and_twin_persist_independently`: a `remember` does not clobber a `twin.save` and vice-versa
  - `test_long_conversation_auto_remembers_consistently`: 20 mixed turns → working holds the last 10, semantic holds all 10 long ones

## Decisions / deviations
- **`update_twin` uses `DigitalTwin.model_validate` over `model_copy(update=...)`.** Pydantic v2's `model_copy(update=...)` does not re-run validation, so `extra="forbid"` and per-field constraints (e.g. `age <= 120`) would be silently bypassed. To enforce the contract, I build a merged dict from `current.model_dump(mode="python")` and re-validate with `DigitalTwin.model_validate(...)`. This means an unknown kwarg *and* an out-of-range value both surface as `pydantic.ValidationError` rather than corrupting the store. `mode="python"` keeps datetimes as `datetime` objects (not ISO strings), avoiding a needless round-trip.
- **Auto-remember threshold is strictly greater-than 50** (per the contract text "if content > 50 chars"). A 50-character turn is *not* auto-remembered; a 51-character one is. There's a dedicated boundary test for both sides (`test_exactly_50_chars_not_auto_remembered`, `test_51_chars_is_auto_remembered`).
- **`update_twin` rejects `user_id` change** as a "reserved field" — changing the key field would orphan the persisted row silently. The test `test_update_twin_rejects_user_id_change` proves both that the call raises AND that the original twin remains intact at the original `user_id`. The reserved-field set is a single-element `frozenset` constant for future-proofing.
- **`remember` injects `user_id` into metadata when the caller omits it.** The semantic store has no implicit per-user partitioning, so a `recall` from one user could surface another user's documents. Injecting `user_id` is the *minimum* hygiene we can do at this layer; full per-user collection isolation is a follow-up.
- **`get_twin` re-raises `KeyError` from the store unchanged** rather than wrapping it. The contract says "raises `KeyError` if not found" and FM-11 says "fail loud, never invent" — wrapping the error would add an extra hop and could swallow message text.
- **Factory has `max_turns` kwarg** even though the brief doesn't show it — it costs nothing and matches the `WorkingMemory` default-override pattern from task 01's tests.
- **Working memory is in-process only and *not* persisted across `MemoryManager.create` instances.** This matches the contract: only semantic + twin are durable. The integration test explicitly asserts `mgr2.get_context() == []` after reload to lock in that design.

## Surprises / gotchas
- **Pydantic v2's `model_copy(update=...)` does not validate.** This is the kind of thing you only learn when you write a test that expects `ValidationError` and get a `pass` instead. Caught immediately by `test_update_twin_rejects_unknown_field` and `test_update_twin_rejects_out_of_range_age`. The fix is documented in the `update_twin` docstring's "Notes" section so the next reader doesn't fall in the same hole.
- **The stdlib TF-IDF fallback tokenizes on whitespace only** (`.lower().split()`), so `"retirement"` and `"retire"` are distinct tokens. My first integration test asserted `"retirement" in r["text"]` for a turn that contained `"retire"`, which failed for this reason. I updated the turn content to include the exact token I was searching for, with a comment explaining the requirement. This is an upstream behavior (in task 02's `semantic.py`), not a bug in this task, but worth knowing for wave-4 agents that build recall queries.
- No `docs/waves/wave-2-gotchas.md` exists yet — the wave-2 brief/gotchas split is not in `docs/waves/`. I did not create one (FM-13 says don't touch docs unless I have a gotcha worth filing). The two surprises above are documented in the report and in code comments; if the orchestrator wants a wave-2-gotchas file, that's a separate triage action.

## Follow-ups (for orchestrator triage — do NOT build now)
- **Per-user semantic isolation.** Today `remember` injects `user_id` into metadata, but `recall` does not filter by it. Wave-4 agents that call `recall` will get documents from every user who ever used the same ChromaDB collection. The fix is either (a) a per-user collection name in the `create` factory, or (b) a `where={"user_id": self._user_id}` filter baked into `recall`. Both are small but a real privacy concern — flagging.
- **Auto-remember metadata should include `turn_index` or `timestamp`** so a recall can reconstruct *when* a fact was learned. The current metadata (`user_id`, `role`, `source`) is enough to deduplicate, not enough to time-order.
- **No `delete_twin` on the facade.** Wave-4 might want to nuke a user; today it has to reach through to `twin_store.delete(self._user_id)`. A `MemoryManager.delete_twin()` would be 3 lines and keep the facade the only thing wave-4 touches.
- **Working memory does not survive a manager reload** (in-process deque). If a wave-4 flow is "user closes browser, comes back tomorrow, expects the agent to remember the conversation", the working layer is the wrong tool and we need a persistent conversation log. Out of scope for this task but worth flagging for the wave-4/wave-5 design discussion.

## Self-check
- [x] Only touched my Writes set: `src/finroot/memory/manager.py`, `tests/unit/test_memory_manager.py`, `tests/integration/test_memory_integration.py` (plus this report). No edits to `working.py` / `semantic.py` / `digital_twin.py` / `__init__.py` (FM-13).
- [x] No fabricated numbers; the auto-remember threshold is contract-defined; all twin / semantic data is from the real stores (FM-11).
- [x] No bare excepts / silent fallbacks — every method propagates errors from the underlying stores unchanged. The only `try/except` in the codebase is in `digital_twin.py` and `semantic.py` (their own contracts, not mine).
- [x] ruff clean, tests green (output above). 50/50 tests pass.
- [x] No secrets committed (FM-07) — there is no LLM key, no API key, no real PII; all user data in tests is synthetic.
