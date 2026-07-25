# HANDOFF — Current State

> Replaced 2026-07-25T19:28Z — hostile stranger-verification loop (this session).

## Snapshot
- **Honest blended score:** **~97-98%** — **not 100%, not frozen**
- **FRB @ `e861de4`:** mean **0.9117** · pass@1 **1.0000** · lift **+168.94%** vs RAG
- **Evidence:** `docs/SCOREBOARD.md` §E (full list of 12 bugs found + fixed this session)
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
| **Now (hostile stranger-verify)** | **~97-98** | **1.00** |

## This loop — genuine hostile/cold verification, not trusting prior reports
Ran real `git clone` + fresh venv (3 independent times) and followed the documented judge
path verbatim, rather than trusting any prior "100%"/"96% done" self-report. Found and fixed
12 real bugs a stranger/judge would have hit — full list in `docs/SCOREBOARD.md` §E. Highlights:
1. **GP-3 (prudence trap) broke on paraphrase** — regex required exact "emergency fund...
   all/entire" phrasing; a natural rewording slipped through with no refusal at all on the
   single most safety-critical golden path. Broadened + re-verified (original, paraphrase,
   and a false-positive check).
2. **Citations UI crashed** — raw `AttributeError` shown to end users instead of citations
   (Python eagerly evaluates `getattr(x, k, x.get(k))`'s default arg even when unneeded).
3. **Silent data clobber** — every query overwrote any existing real digital-twin record
   with demo/fixture data; now only seeds if none exists.
4. **`fastapi`/`uvicorn` missing from all dependency manifests** — API smoke crashed on
   a genuinely fresh install; invisible on any machine that already had them globally.
5. **Two structurally-broken tests** (`test_metrics_freshness.py`) — one required a tracked
   file to embed its own future commit hash (impossible), one had a 3-hour wall-clock cliff
   that fails for any judge running tests later. Replaced with a git-ancestry check.
6. **CI shallow-clone bug** — the new ancestry check needs `fetch-depth: 0`, not GitHub
   Actions' default depth-1 checkout. Fixed in `ci.yml`/`test.yml`.
7. **Docker healthcheck used `curl`**, not installed in the image — container permanently
   "unhealthy" despite serving correctly. Fixed; verified `(healthy)` twice.
8. **`validate.sh` had two stale checks** failing the `docs_sync` CI workflow on every push
   (forced KIMI.md/AGENTS.md byte-identical to CLAUDE.md; scanned all historical waves for
   FM-13 collisions). Fixed to match how the project legitimately evolved.
9. **README overstated LangChain** — code only uses LangGraph's StateGraph; corrected
   wording (verified via `grep -rn "from langchain\." src/` → zero hits).

## Prove green
```bash
make smoke
bash scripts/judge_dry_run.sh
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1
# expect pass@1=1.0000 mean≈0.9117
docker-compose up -d && sleep 30 && docker-compose ps   # expect (healthy)
docker-compose down
```
All of the above were re-verified on **independent fresh `git clone`s**, not just the local
working tree, after every fix landed.

## Still open for freeze
1. **Human freeze bet** — the one thing this session cannot self-certify. Everything
   mechanical (clean commit, true cold-clone, docker, security review, CI) is done.
2. Continued hostile-audit surface may still exist — 3 more parallel audit passes
   (stability soak, LangChain wording, CI workflow audit) ran this session and each found
   something real; there is no guarantee the surface is now exhausted, only that everything
   found so far is fixed and verified.

**Do not claim submission 100% — that requires the human freeze bet.**
