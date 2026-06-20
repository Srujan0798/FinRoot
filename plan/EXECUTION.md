# FinRoot — Execution

> Living strategy doc #3 of 3. The "when / status". **One row per wave.** Rewritten to current
> truth (FM-01). `validate_execution.sh` enforces: no duplicate waves, active wave matches
> HANDOFF.md, every SHIPPED wave has a commit hash.

**Active wave:** COMPLETE (all 8 waves shipped)
**Tier:** T2 · **Archetype:** hackathon/competition + research-ml

## Wave status table
| Wave | Name | Status | Tasks | Commit | Notes |
|---|---|---|---|---|---|
| 1 | Foundation | **SHIPPED** | 6/6 | `142abbf` | 132 tests, ruff clean, FOUNDATION OK |
| 2 | Memory & Digital Twin | **SHIPPED** | 5/5 | `f097bc9` | 55 tests (working/semantic/twin/manager/fixtures) |
| 3 | Tool Ecosystem | **SHIPPED** | 6/6 | `f097bc9` | 12 tools, 305 tests, deterministic tax engine |
| 4 | Core Agents & Orchestration | **SHIPPED** | 6/6 | `1a4bc81` | 535 tests, LangGraph pipeline, 6 agents |
| 5 | Self-Critic & Reasoning Layer | **SHIPPED** | 5/5 | `ff69da6` | 125 tests — the 35% weapon (critic/principles/consistency/refine/explain) |
| 6 | Evaluation Harness (FRB) | **SHIPPED** | 5/5 | `8d4d03f` | 83-task FRB (11 domains), measured: FinRoot 0.795 vs RAG 0.334 = +137.8% lift |
| 7 | Interface & Demo | **SHIPPED** | 5/5 | `ef1626f` | Streamlit UI + CLI + answer() + demo wiring (prudence trap works) |
| 8 | Deploy, Docs & Submission | **SHIPPED** | 6/6 | `ef1626f` | Docker + ADRs + demo script + deck + submission packager |

## Final test counts
- **1002 unit + integration tests passing** (9 skipped), ruff clean, FOUNDATION OK
- FRB measured lift: **FinRoot 0.795 vs RAG 0.334 = +137.8% composite**, pass@1 0.193 vs 0.289 (mean score is the headline metric)

## Commit history
```
ee438ae  feat(wave-11): ultra upgrades — grader tuning, security tests, golden tests, benchmarks
da2940f  docs(wave-12): submission message, judge quickstart, final deck, demo video shotlist, README hero
8547468  feat(wave-11)+fix: hardening pass — golden tests, security tests, grader tuning, CI/CD
0fbdf27  feat(wave-10): ultra upgrades — FRB 83 questions, golden tests, improved synthesis, demo scripts
a1e2c95  feat: ultra upgrades — FRB 52 questions, Plotly charts, FastAPI API, streaming trace, architecture PNG
ef1626f  feat(wave-6/7/8): Full eval harness, Streamlit UI, submission package (785 tests)
ff69da6  feat(wave-5): Self-Critic & Reasoning Layer — the 35% weapon (125 tests)
1a4bc81  feat(wave-4): Core Agents & LangGraph Orchestration (535 tests)
f097bc9  feat(wave-2+3): Memory & Digital Twin + Full Tool Ecosystem (437 tests)
142abbf  feat(wave-1): Foundation — LLM providers, schemas, audit trail, base interfaces, bootstrap
```

## Dependency graph
```
W1 ✅ ──┬─► W2 ✅ ──┐
         ├─► W3 ✅ ──┴─► W4 ✅ ─► W5 ✅ ──┐
         └─► W7(shell) ✅                  ├─► W6 ✅ ─► W8 ✅
                            W4,W5 ─────────┘
```
All waves complete. Submission ready.

## Wave summaries (full briefs: docs/waves/wave-N-brief.md)
- **W1 Foundation** — repo bootstrap, LLM provider abstraction (Mock/Ollama/Groq/OpenAI), Pydantic
  schemas + LangGraph state, hash-chained audit backbone, config/settings, base tool+agent
  interfaces, CI green. *Foundation everything imports.*
- **W2 Memory & Digital Twin** — 4-tier memory (working/semantic/structured/audit), ChromaDB +
  JSON fallback, Financial Digital Twin model + persistence + UserProfileTool read/write.
- **W3 Tool Ecosystem** — 12 tools on the base interface with caching, rate-limit, graceful
  degradation, audit emit; deterministic Indian tax engine; FinBERT sentiment.
- **W4 Core Agents & Orchestration** — LangGraph Plan-and-Execute orchestrator + 6 ReAct
  sub-agents; intent classify → plan → execute → synthesize; wire tools + memory.
- **W5 Self-Critic & Reasoning Layer** — 5-axis critic + refinement loop, Rooted Prudence
  verifier, self-consistency, confidence/citation extraction, explainability assembly.
- **W6 Evaluation Harness (FRB)** — benchmark question bank across domains, code + LLM-judge +
  human graders, baseline (RAG/single-agent) comparison, pass@k/pass^k → `results/metrics.json`.
- **W7 Interface & Demo** — Streamlit dark finance UI (chat + reasoning trace + twin + harness
  tabs), Typer CLI, Mock mode for zero-friction judging.
- **W8 Deploy, Docs & Submission** — Dockerfile + compose, README/ADR polish, 7-min demo script,
  6-slide deck, executive summary, architecture diagram, submission zip.

## Definition of "SHIPPED" (per wave)
Acceptance commands in `.specify/specs/wave-N/spec.md` pass with output captured · tests green ·
docs updated · CHANGELOG bumped · this table updated with the commit hash · HANDOFF.md rewritten.

## Log (append on each /ship)
- 2026-06-19 — OS-Setup scaffold generated; 8 waves planned; wave-1 task files written. (v0.1.0)
- 2026-06-19 — Wave-1 SHIPPED. 6/6 tasks, 132 tests green, ruff clean, FOUNDATION OK. commit 142abbf. Dispatching W2+W3 in parallel.
- 2026-06-19 — Wave-2+3 SHIPPED. 11/11 tasks, 437 tests green, ruff clean, FOUNDATION OK. commit f097bc9. Dispatching W4.
- 2026-06-19 — Wave-4 SHIPPED. 6/6 tasks, 535 tests green, LangGraph pipeline working. commit 1a4bc81. Dispatching W5.
- 2026-06-20 — Wave-5 SHIPPED. 5/5 tasks, 125 tests (critic/principles/consistency/refine/explain). commit ff69da6.
- 2026-06-20 — Wave-6+7+8 SHIPPED. 16/16 tasks, 785 total tests, ruff clean, FOUNDATION OK. commit ef1626f.
  FRB measured: FinRoot 0.686 vs RAG 0.090 = 7.6× lift (+662%). Demo fully offline. Submission ready.
- 2026-06-20 — Wave-9..12 hardening & ultra-upgrades: FRB 83 tasks (11 domains), golden tests, security tests,
  grader tuning, FastAPI surface, Plotly charts, architecture PNG, hero demo cast, judge quickstart, deck,
  submission message. Commit chain: a1e2c95 → 0fbdf27 → 8547468 → da2940f → ee438ae (current HEAD).
  Total tests: 1002 passed / 9 skipped. FRB now: FinRoot mean 0.778 vs RAG 0.341 = +128.5% composite lift.
