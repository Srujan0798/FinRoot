# Report wave-2/01 — WorkingMemory (ConversationBufferWindow)

## Result
DONE

## What I built
- `src/finroot/memory/working.py` — `WorkingMemory` class (sliding-window, thread-safe, JSON-serialisable) plus internal frozen `_Turn` Pydantic v2 model and the `Role` `Literal` type alias.
- `src/finroot/memory/__init__.py` — re-exports `WorkingMemory` and `Role`; docstring enumerates the package's planned public surface for tasks 02/03/04 (they will append their re-exports here as they merge).
- `tests/unit/test_working_memory.py` — 48 tests covering construction, role/content validation, sliding window, get-messages immutability, clear, to_json/from_json round-trip, from_json failure modes, frozen `_Turn` enforcement, and three thread-safety tests (no-message-loss, maxlen-invariant under concurrent writers, no-torn-state for concurrent readers).

## Acceptance evidence (real output, this session)

```bash
$ PYTHONPATH=src python3 -m pytest tests/unit/test_working_memory.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_loop=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 48 items

tests/unit/test_working_memory.py ...................................... [ 79%]
..........                                                               [100%]

============================== 48 passed in 1.68s ==============================
---EXIT:0---

$ ruff check src/finroot/memory/working.py src/finroot/memory/__init__.py
All checks passed!
---EXIT:0---

$ ruff check src/finroot/memory/working.py src/finroot/memory/__init__.py tests/unit/test_working_memory.py
All checks passed!
---EXIT:0---
```

## Tests
- 48 tests added · **48 passed / 0 failed** in 1.68s
- Coverage of the contract surface: `__init__` validation (3 cases + 1 bool-guard + 4 non-int cases), `add` happy + role rejection (6 cases) + content type rejection, sliding window (drop-oldest, mixed-roles, max_turns=1), `get_messages` freshness (list + dict copy), `clear` (basic, no-op on empty, reusability), `to_json`/`from_json` round-trip (preserves order+capacity, empty buffer, post-drop history, JSON shape, unicode), `from_json` failure modes (8 distinct ValueError paths), internal `_Turn` frozen + role validation, three thread-safety tests using `threading.Barrier` / `threading.Event`.
- No external test fixtures; the threading tests are self-contained and use the in-memory buffer only.

## Decisions / deviations
- **Used `collections.deque(maxlen=…)` for the sliding window.** The stdlib FIFO drop is atomic per-operation, so the lock only needs to guard the `validate → append` sequence in `add()` (and the compound reads/writes in `to_json`/`get_messages`/`clear`). This is the smallest correct solution and matches the contract's thread-safety requirement.
- **Internal `_Turn` Pydantic v2 model is `frozen=True, extra="forbid"`.** The public API still returns plain `{"role": ..., "content": ...}` dicts per the contract, but the buffer itself stores typed, immutable values so role/content are validated at the boundary. The `_Turn` is intentionally not re-exported from `__init__.py` — it is an implementation detail.
- **`Role` is exposed as a `Literal["user", "assistant", "tool"]` type alias.** It is in `__all__` for downstream code that wants a static type to annotate against, but the public `add(role: str, content: str)` signature matches the contract.
- **Bool-rejection in `__init__`.** `bool` is a subclass of `int` in Python, so `WorkingMemory(max_turns=True)` would otherwise be accepted as `max_turns=1`. Explicitly rejecting `bool` keeps the constructor honest.
- **Empty-string content is allowed.** System/tool messages and terse "ok" replies are legitimate and the contract specifies `str` without `min_length=1`.
- **JSON output uses `ensure_ascii=False, separators=(",", ":")`.** Keeps the payload compact and preserves non-ASCII content faithfully. `to_json`/`from_json` round-trips unicode (verified by a dedicated test).
- **`from_json` is strict.** It fails loud (FM-11) on: non-string input → `TypeError`; bad JSON → `ValueError`; non-object payload → `ValueError`; missing keys → `ValueError`; non-list turns → `ValueError`; non-dict turn → `ValueError`; turn without role/content → `ValueError`; unknown role → `ValueError` (re-raised from `add`); invalid `max_turns` → `ValueError` (re-raised from `__init__`). No silent fallbacks.
- **`__init__.py` keeps the package import-safe while sibling tasks have not landed yet.** The contract file map assigns this file to task 01 only, so I export only `WorkingMemory` + `Role` and document the rest in a docstring. Tasks 02/03/04 will append their re-exports here as they merge (the orchestrator coordinates that). My first draft used a PEP 562 `__getattr__` for lazy re-exports; I removed it because it tried to read `globals().get("__loaded_modules__", ...)` which is never set, so it would have raised `AttributeError` for every sibling import — a misfeature. The current plain-import design is correct.

## Surprises / gotchas
- **Initial test run hung indefinitely on `test_concurrent_reads_during_writes_never_observe_torn_state`.** I had a logic bug: I tried to `join()` the writer threads *before* setting the `stop` event, so the writers (which loop `while not stop.is_set()`) ran forever and pytest's 120s default timeout fired. Fixed by joining the *readers* first (their 200-iter loop terminates quickly), then setting `stop`, then joining the writers. The fix is captured in the test source; not added to `docs/waves/wave-2-gotchas.md` because it was a test bug rather than a project-wide gotcha other waves would hit.
- **No `docs/waves/wave-2-gotchas.md` file exists yet.** If the orchestrator expects this to be created by the first worker of the wave, that should be coordinated across tasks 01–05; I have not created it (stayed strictly in my Writes set).
- **Git status shows sibling tasks' untracked files in `src/finroot/memory/` (`semantic.py`, `digital_twin.py`) and `tests/unit/` (`test_semantic_memory.py`, `test_digital_twin.py`).** I did not touch them; `git status --short` for my changed set is exactly the three files in the Writes block (plus their parent directories appearing because the dirs are new at HEAD). FM-13 holds.

## Follow-ups (for orchestrator triage — do NOT build now)
- **LangChain message conversion helper.** The task brief's "integrates with LangChain memory" hint suggests an eventual `to_lc_messages() -> list[BaseMessage]` returning `HumanMessage`/`AIMessage`/`ToolMessage` for direct prompt injection. MemoryManager (task 04) is the right place to do this — it can call into `langchain-core` once, behind the facade — but if wave-4 wants it on `WorkingMemory` directly, it's a 10-line addition (`pip install langchain-core` is already a hard dep).
- **Token-budget truncation.** Current window is *turn*-count based. A future `max_tokens` mode (tiktoken-based) would be useful for long-context models; not in this wave's contract.
- **Persistence to disk.** Today the buffer is in-process only. The `to_json`/`from_json` pair is the seed for an on-disk log, but the actual write-on-add behaviour is better handled by the audit layer (which already gives tamper-evidence). Probably BACKLOG, not a wave concern.
- **The `__init__.py` re-export choreography** between tasks 01/02/03/04/05 needs orchestrator coordination. Suggest a single-line "append your import here" rule in the next wave brief, or assign a merge-order where one task updates the `__init__` last.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13) — `git status --short` confirms `src/finroot/memory/__init__.py`, `src/finroot/memory/working.py`, `tests/unit/test_working_memory.py` are the only `?? ` files I authored.
- [x] No fabricated numbers; tool outputs cited (FM-11) — pure logic, no external data; Pydantic validates all boundary values; `from_json` propagates `__init__`/`add` validation.
- [x] No bare excepts / silent fallbacks — every `except` clause either re-raises as `ValueError` (with the original chained via `from`) or re-raises unconditionally.
- [x] ruff clean, tests green (output above) — `ruff check` on the three files I wrote returns `All checks passed!`; `pytest` returns `48 passed`.
- [x] No secrets committed (FM-07) — no env vars, no keys, no prompts; the only string literals in the code are role names and the type `Literal`.
