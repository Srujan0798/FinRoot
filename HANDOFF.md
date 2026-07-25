# HANDOFF — Current State

> Replaced 2026-07-25T20:04Z — hostile stranger-verification loop, round 2 (this session).

## Snapshot
- **Honest blended score:** **~97-98%** — **not 100%, not frozen**
- **FRB @ `635ebd5`:** mean **0.9117** · pass@1 **1.0000** · lift **+168.94%** vs RAG
- **Evidence:** `docs/SCOREBOARD.md` §E-F (full list of 15 bugs found + fixed this session)
- **Plan:** `work/ETERNAL_FINAL_PLAN.md` · **Scoreboard:** `docs/SCOREBOARD.md`

## Trajectory
| Stage | % | pass@1 |
|---|---:|---:|
| Audit | 68 | 0.46 |
| Phase 1 GP | 83 | — |
| Domain FRB | 91 | 0.63 |
| Conf soft + tax HIGH | ~94.5 | 0.87 |
| Tax residual | ~95.5 | 1.00 |
| Mean + judge dry-run | ~96 | 1.00 |
| Hostile stranger-verify round 1 | ~97-98 | 1.00 |
| **Now (round 2 — remaining GP paraphrase + deps)** | **~97-98** | **1.00** |

## This loop — genuine hostile/cold verification, not trusting prior reports
Ran real `git clone` + fresh venv (**4 independent times across 2 rounds**) and followed the
documented judge path verbatim, rather than trusting any prior "100%"/"96% done" self-report.
Found and fixed **15 real bugs** a stranger/judge would have hit — full list in
`docs/SCOREBOARD.md` §E-F. Round 2 additions on top of round 1's 12:
1. **GP-1 (portfolio) misrouted to news_impact on paraphrase** — a rewording without
   "portfolio"/"rebalance"/"allocation" scored 0 for PORTFOLIO while bare "stock" alone won
   NEWS_IMPACT outright. Broadened keyword triggers; verified original + paraphrase.
2. **GP-2 (tax) three compounding word-form gaps** — "a lakh" (no digit), "two years" (word
   not digit), "equities" (plural not matching substring "equity") all fell through to a
   non-answer instead of computing tax. Fixed all three; verified original + broken paraphrase
   + a second already-working paraphrase (no regression).
3. **Disclosed 14 real PYSEC-backed dependency CVEs** (RCE-class in `langgraph-checkpoint`,
   SSRF/path-traversal in `langchain-core`) found via a live `pip-audit` pass. **Not fixed** —
   the only fixes ship in major version bumps this repo's own version ceilings block, and an
   untested major upgrade of the core orchestration framework under time pressure is a worse
   risk than a disclosed, scoped known-issue. Checked real exploitability directly: no
   checkpointer is compiled into the StateGraph, chromadb runs embedded-only — both most
   severe advisory classes are present-but-unreachable in actual usage, not silently ignored.
   Full detail + recommendation for a future dedicated upgrade wave: `docs/SCOREBOARD.md` §F.

Round 1's 9 fixes (still in effect): GP-3 paraphrase brittleness, citations UI crash, silent
digital-twin data clobber, missing fastapi/uvicorn deps, structurally-broken freshness tests,
CI shallow-clone bug, docker healthcheck curl bug, stale validate.sh checks, LangChain
overstatement — see prior HANDOFF revisions in git history or `docs/SCOREBOARD.md` §E for detail.

## Prove green
```bash
make smoke
bash scripts/judge_dry_run.sh
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1
# expect pass@1=1.0000 mean≈0.9117
docker-compose up -d && sleep 30 && docker-compose ps   # expect (healthy)
docker-compose down
```
All of the above were re-verified on **4 independent fresh `git clone`s**, not just the local
working tree, after every fix landed — most recently confirmed at HEAD `75f23e2` before the
final housekeeping regen to `635ebd5`.

## Still open for freeze
1. **Human freeze bet** — the one thing this session cannot self-certify. Everything
   mechanical (clean commit, true cold-clone ×4, docker, security review + honest CVE
   disclosure, CI) is done.
2. **Dependency version-ceiling upgrade** (see docs/SCOREBOARD.md §F) — real, disclosed,
   deliberately deferred rather than rushed. Needs a dedicated wave with full regression.
3. Continued hostile-audit surface may still exist — every audit pass dispatched this session
   found something real (2 rounds, ~9 subagents); there is no guarantee the surface is now
   exhausted, only that everything found so far is fixed, disclosed, or explicitly deferred
   with reasoning.

**Do not claim submission 100% — that requires the human freeze bet.**
