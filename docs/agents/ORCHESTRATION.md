# Agent Orchestration Plan — assigning your swarm to FinRoot

> This is the map you (Srujan) use to assign your agents. The orchestrator (Claude/Kimi) plans and
> reviews; **your worker agents implement**. This doc shows the roles, the wave→task→role mapping,
> the parallelism, and exactly how to hand work off. (The orchestrator does NOT do the workers' jobs.)

## The split (never blurred)
- **Orchestrator (Tier 1):** you run ONE Claude Code or Kimi session in this repo. It plans waves,
  writes `work/<wave>/*.md` task files, reviews reports, runs acceptance, merges, ships. No `src/` code.
- **Workers (Tier 2 = your agents):** each takes ONE task file + `work/WORKER_PROMPT.md`, implements
  into its `Writes` set, writes a report. Stateless, parallel.

## Recommended worker roles (map these to your actual agents)
| Role | Specialty | Waves it shines in |
|---|---|---|
| **types/architecture** | Pydantic, LangGraph state, interfaces | W1·02/05, W4·05, W5 |
| **backend/infra** | providers, config, persistence | W1·01/04, W2 |
| **security/backend** | audit chain, safety, secrets | W1·03, audits |
| **ML/data** | Chroma, FinBERT, baselines | W2·02, W3·02, W6·03 |
| **agent engineer** | ReAct/LangChain sub-agents | W4·02/03/04 |
| **reasoning/LLM** | critic, refine, principles, consistency | W5 (all), W6 |
| **eval engineer** | graders, harness, metrics | W6 |
| **frontend** | Streamlit, CLI | W7 |
| **devops/docs** | Docker, CI, ADRs, demo, zip | W1·06, W8 |

You don't need 9 agents — one capable agent can wear several hats across waves. The point is the
**task files are self-contained**, so any agent can pick up any task that fits its hat.

## Wave-by-wave dispatch order + parallelism
```
W1 Foundation (6 tasks)
   └─ 02 schemas FIRST (freeze contract) → then 01,03,04,05 in PARALLEL → 06 last
W2 Memory (5)  ┐  dispatch W2 + W3 TOGETHER after W1 ships
W3 Tools (6)   ┘  (W3 is the widest fan-out — up to 6 agents at once)
W4 Agents (6)  → after W2+W3; 02,03,04 parallel, then 05 orchestrator, then 06 synth
W5 Reasoning (5) → after W4; 01→02, 03, 04 parallel, then 05
W6 Evals (5)   → after W4+W5
W7 Interface (5) → UI shell after W1; full after W4/W5
W8 Submit (6)  → after all
```
Peak parallelism: **W3 (6 agents)**. Typical: 3–5 agents at once.

## The handoff ritual (per wave)
1. **You → orchestrator:** "Dispatch wave-N." (For W1 the task files already exist.)
2. **Orchestrator → you:** the list of `work/wave-N/0X-*.md` files + confirmation that write-sets are
   disjoint (parallel-safe).
3. **You → each worker agent:** paste `work/WORKER_PROMPT.md` + ONE task file. Run them in parallel.
4. **Worker → repo:** implements its `Writes` set, writes `work/reports/wave-N/0X-*.report.md`.
5. **You → orchestrator:** "Review wave-N." It re-runs acceptance, decides APPROVE/REVISE/REJECT.
6. **Orchestrator:** merges approved tasks, then `/ship` the wave. Activates the next wave.

## Collision safety (why parallel is safe)
Every task lists a disjoint `Writes` set and a `Forbid` list (FM-13). Shared interfaces are frozen as
`.specify/specs/<wave>/contracts/*.md` BEFORE dispatch, so no two agents define the same type. If two
pending tasks ever share a path, the orchestrator re-partitions before dispatch (`validate.sh`).

## What each side must NOT do
- Orchestrator must not write `src/` (no implementation).
- Workers must not touch `orchestrator/`, `plan/`, `docs/`, `.specify/`, or another task's files.
- Neither fabricates financial numbers or rounds "partial" up to "done".

## Quick start (right now)
W1 is ready. Open the orchestrator → "Dispatch wave-1" (files exist) → open up to 5 worker windows →
paste `WORKER_PROMPT.md` + each `work/wave-1/0X-*.md` (02 first). Reports land in
`work/reports/wave-1/`. Then "Review + ship wave-1."
