# OS-Setup — Universal Agentic Project Kickstart

> **What this is.** A single self-sufficient markdown file that turns ANY project brief into a complete, dual-tier agentic project structure. Paste this file + your project details into Claude or Kimi, and you get the entire repo pre-filled, ready to start shipping with OpenCode CLI workers in parallel windows.
>
> **Built from.** Four deep methodology iterations + two dedicated specifications + live web research (May 2026) across Anthropic Skills (agentskills.io), Boris Cherny's Claude Code best practices, Karpathy CLAUDE.md, 12-Factor Agents, 5 canonical patterns, SuperClaude (30 commands), BMAD Method, kmshihab Claude OS pattern, Spec-Kit, Kiro, MCP, A2A, mattpocock skills, OpenClaw, Hermes, Letta, and 40+ tools on the agentskills.io standard.
>
> **Plus empirical lessons from 5 real shipping projects:** rfq2boq (NLP/ML), swa-erp (Python+React internal ERP — already shipped wave-1 + wave-2), NRG (production-grade with DPDP compliance, observability, SLOs), Ultra-Dex-Orc (workflow-driven multi-agent with declarative JSON workflows + per-workflow state files), DRO-FairML (research project).
>
> **Plus the very latest Anthropic engineering posts (Q1+Q2 2026):**
> - **"Scaling Managed Agents: Decoupling the brain from the hands"** (Apr 2026) — formal Brain/Hands/Session triad
> - **"Demystifying evals for AI agents"** (Jan 2026) — eval-driven development, pass@k / pass^k, anti-patterns
> - **"How we built Claude Code auto mode"** (Mar 2026) — safe skip-permissions for routine work
> - **"Harness design for long-running application development"** (Mar 2026) — stateless harness + durable session log
> - **"How we contain Claude across products"** — blast-radius as first-class concept
> - **Skills 2026 unification** — commands are now skills; `.claude/commands/X.md` and `.claude/skills/X/SKILL.md` both create `/X`. `allowed-tools` frontmatter is canonical. Skills can run in their own sub-agent context.
>
> **Version.** v2.0-standalone — Jun 2026. The complete single-file edition: everything in v1.3 PLUS the three systems that make it adapt and self-guard — the **Failure-Mode Guardrails** (§13), the **Archetype Engine** (§14), and the **Adaptor Engine** (§15). This single file now matches the OS-Setup folder's power for a fast, paste-and-go start. (The `OS-Setup/` folder remains the expandable multi-file edition with executable validator scripts; this file embeds their rules inline.)

---

## 0. How to use this file

1. **Open Claude Code or Kimi.** Either works — they're interchangeable.
2. **Paste this file** at the top of your conversation.
3. **Paste the project brief** (PDF text, one-paragraph scope, or just a goal). Add context if you have it: deadline · audience · tech preference · must-not-do · success criteria.
4. **Say**: *"Use OS-Setup v2.0-standalone. Run the Adaptor Engine (§15): detect the archetype (§14), pick a tier (§1.5), wire the relevant failure-mode guardrails (§13), then generate the complete project structure for this brief."*
5. The orchestrator detects the **archetype**, picks a **tier**, pulls only what fits, wires the **guardrails**, and creates the `<project-name>/` folder filled in for your project.
6. You open OpenCode CLI workers in parallel, paste task files from `work/`, and start shipping.

> **The fast path:** for a quick start, steps 3–4 collapse to: paste brief → "adapt and scaffold this." The engine asks ≤4 questions only if genuinely ambiguous, else proceeds.

---

## 1. The Two-Tier Agentic Methodology

```
┌──────────────────────────────────────────────────────────────────┐
│  TIER 1 — ORCHESTRATOR  (Claude OR Kimi, interchangeable)        │
│                                                                  │
│  • Reads project state, specs, reports                           │
│  • Writes task files into work/                                  │
│  • Reviews worker reports                                        │
│  • Merges output, updates state                                  │
│  • One process at a time — single source of truth                │
│  • If Claude is down, switch to Kimi. Same files, same workflow. │
└────────────────────────────┬─────────────────────────────────────┘
                             │ task file (self-contained brief)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  TIER 2 — WORKERS  (OpenCode CLI in multiple parallel windows)   │
│                                                                  │
│  • Receive ONE self-contained task file                          │
│  • Use their OWN skills (skills.sh / Claude built-in /           │
│    agentskills.io online — NOT this project's orchestrator skills)│
│  • Execute, write code/data/models to repo                       │
│  • Write standardized report to work/reports/                    │
│  • Stateless across tasks; parallel by default                   │
└──────────────────────────────────────────────────────────────────┘
```

**Core rule.** The orchestrator never executes implementation. Workers never plan. The handoff is `work/<wave>/<task>.md` → `work/reports/<wave>/<task>.report.md`.

**Terminology.** Units of work are **waves** (preferred) or **slices**. A wave is a coherent end-to-end deliverable shipped before the next wave begins. Waves break into 4–8 tasks dispatched to parallel workers.

### 1.5 Project Tiers (NEW in v1.2)

Pick the smallest tier that fits. Bigger tier = more files = more discipline = more overhead.

| Tier | Use when | Adds beyond previous tier |
|---|---|---|
| **T0 — Minimum** | Solo experiment, throwaway script, weekend hack | CLAUDE.md + work/ + plan/PRD only (10 files) |
| **T1 — Standard** | Internal tool, small team, MVP (default) | Full §2 structure: orchestrator/, .specify/, plan/, docs/ — ~90 files |
| **T2 — Production** | Real customers, observability matters, ops on-call | Adds docs/operational/, docs/audits/<date>/, HALL_OF_SHAME.md, BACKLOG.md, performance budgets in CI |
| **T3 — Enterprise** | Compliance required (DPDP/GDPR/HIPAA), audited | Adds docs/compliance/, periodic SECURITY_AUDIT.md, certificates/, multi-Dockerfile, env-specific docker-compose |
| **T4 — Startup launch** | Customer-facing product seeking PMF | Adds STARTUP_ROADMAP.md, docs/business/, STAKEHOLDER_UPDATE.md, ROADMAP.md (outward), demo_video_script.md, deliverables/ subfolders |

Tiers are **additive**. T4 includes T3 includes T2 includes T1. Default to T1. Bump tier when a need is real, not speculative.

### 1.6 — Anthropic's Brain/Hands/Session Triad (NEW in v1.3)

Per Anthropic's April 2026 "Scaling Managed Agents" post, the modern agent architecture decouples three components:

```
┌─────────────────────────────────────────────────────────────────────┐
│  BRAIN  — Claude/Kimi model + harness (stateless reasoning loop)    │
│          • In our setup: Claude Code or Kimi running the            │
│            orchestrator/ apparatus                                  │
│          • Can crash and recover via wake(sessionId)                │
└──────┬─────────────────────────────────────────────────────┬────────┘
       │ execute(name, input) → string                       │
       │                                                     │ emitEvent(id, event)
       ▼                                                     ▼
┌─────────────────────────────────────┐    ┌──────────────────────────────────┐
│  HANDS  — sandboxes + tools         │    │  SESSION  — durable event log    │
│          (disposable; "cattle")     │    │           (append-only)          │
│  • OpenCode CLI worker windows      │    │  • orchestrator/memory/session/  │
│  • MCP servers                      │    │    <wave>-<task>.events.jsonl    │
│  • Docker sandboxes (T3+)           │    │  • survives orchestrator restart │
│  • Hosted tools (search, browser)   │    │  • drives wake() resumption      │
└─────────────────────────────────────┘    └──────────────────────────────────┘
```

**How our setup maps to this triad:**

| Anthropic primitive | Our equivalent |
|---|---|
| **Brain** | Claude Code or Kimi orchestrator (interchangeable) reading `orchestrator/` |
| **Hands** | OpenCode CLI worker windows + MCP servers + (T3) Dockerfile.sandbox |
| **Session** | `orchestrator/memory/session/<wave>-<task>.events.jsonl` (append-only) |
| `execute(name, input)` | the task brief in `work/<wave>/<task>.md` (uniform interface) |
| `emitEvent(id, event)` | append to events.jsonl on every tool use, review, merge |
| `wake(sessionId)` | re-open Claude Code in the same dir; HANDOFF.md + events.jsonl + MEMORY.md restore context |
| `provision({resources})` | open a new OpenCode CLI window or `make worker-N` |
| credentials outside sandboxes | `.env` (gitignored) loaded into harness; never into worker sandboxes |

**Three failure modes covered:**
1. **Brain crash** → reopen Claude Code → reads events.jsonl → resumes
2. **Hand crash** → that one OpenCode window dies → provision a new window with same task brief
3. **Session lost** → the only thing that breaks the system; events.jsonl is the safety net

This is why we *never* couple state into worker containers and why `work/` + `events.jsonl` is the durable record.

---

## 2. The Complete File Structure

```
<project-name>/
├── README.md                          # entry point + how to run
├── CLAUDE.md                          # ★ ROOT — auto-loaded by Claude Code (Boris pattern)
├── KIMI.md                            # ★ ROOT — IDENTICAL to CLAUDE.md (interchangeable)
├── AGENTS.md                          # alias for CLAUDE.md (Cursor + Codex compat)
├── HANDOFF.md                         # ★ ROOT — switching sessions/orchestrators
├── HIERARCHY.md                       # ★ ROOT — repo map + ownership
├── HOW_TO_RUN.md                      # dual-tier workflow in plain language
├── CHANGELOG.md                       # version history (Keep a Changelog format)
├── CONTRIBUTING.md                    # how to contribute
├── BACKLOG.md                         # ⊕T2: parked ideas, untimed
├── HALL_OF_SHAME.md                   # ⊕T2: failure pattern archive (learning, NOT blame)
├── ROADMAP.md                         # ⊕T4: outward-facing long-term roadmap
├── STARTUP_ROADMAP.md                 # ⊕T4: vision + ICP + GTM + pricing experiments
├── OS_SETUP.md                        # ← this file, kept for regeneration
│
├── .claude/                           # ★ MINIMAL — Boris's rule, don't over-build
│   └── settings.local.json            # permissions, MCP, auto-mode
│
├── orchestrator/                      # TIER 1 apparatus (deep, lazy-loaded)
│   ├── ROLE.md
│   ├── core/                          # lazy-loaded governance (≥9 files)
│   │   ├── identity.md
│   │   ├── dispatch-protocol.md
│   │   ├── review-protocol.md
│   │   ├── 12-factor.md
│   │   ├── 5-patterns.md
│   │   ├── karpathy-rules.md
│   │   ├── governance.md              # T0/T1/T2/T3 risk tiering
│   │   ├── context-budget.md
│   │   └── scope-guard.md
│   ├── commands/                      # slash commands (start with 10, grow)
│   │   ├── plan.md  dispatch.md  review.md  merge.md  ship.md
│   │   ├── status.md  next.md  handoff.md  audit.md  reflect.md
│   │   └── (T2+: operator.md  optimizer.md  find-skills.md  fact-checker.md
│   │           prompt-master.md  decision-toolkit.md  mcp-builder.md
│   │           process-interviewer.md  second-brain.md  routines.md)
│   ├── skills/                        # orchestrator-only skills (≥12 SKILL.md)
│   │   ├── write-task-file/SKILL.md
│   │   ├── plan-wave/SKILL.md
│   │   ├── review-report/SKILL.md
│   │   ├── merge-work/SKILL.md
│   │   ├── triage/SKILL.md
│   │   ├── to-prd/SKILL.md
│   │   ├── to-issues/SKILL.md
│   │   ├── status-report/SKILL.md
│   │   ├── diagnose/SKILL.md
│   │   ├── verify-work/SKILL.md
│   │   ├── zoom-out/SKILL.md
│   │   ├── caveman/SKILL.md
│   │   └── self-evolve/SKILL.md
│   ├── agents/                        # sub-agents (REGISTRY.md + ≥4 files)
│   │   ├── REGISTRY.md
│   │   ├── codebase-explorer.md
│   │   ├── verifier.md
│   │   ├── interviewer.md
│   │   ├── brief-writer.md
│   │   └── (T2+: security-reviewer.md  deep-research.md  perf-reviewer.md)
│   ├── hooks/                         # deterministic auto-actions (≥7 scripts)
│   │   ├── session-start.sh
│   │   ├── pre-tool-use.sh
│   │   ├── mcp-security-gate.sh
│   │   ├── block-secrets.sh
│   │   ├── block-destructive.sh
│   │   ├── post-merge-format.sh
│   │   └── stop.sh
│   ├── recipes/                       # parameterized YAML workflows
│   │   ├── new-wave.yaml
│   │   ├── bugfix.yaml
│   │   └── (add per project)
│   ├── rules/                         # path-scoped rules
│   │   ├── python.md  typescript.md  security.md  docs.md
│   ├── memory/                        # auto-memory + MEMORY.md + states + session log
│   │   ├── MEMORY.md
│   │   ├── states/                    # ⊕T2: per-workflow durable state JSON
│   │   │   ├── wave-N-state.json
│   │   │   ├── bugfix-state.json
│   │   │   └── (one per active workflow)
│   │   └── session/                   # ⊕T1: Anthropic Brain/Hands/Session pattern
│   │       ├── <wave>-<task>.events.jsonl   # append-only durable event log
│   │       └── INDEX.md                     # which session corresponds to what
│   └── scripts/                       # ≥3 utility scripts
│       ├── validate.sh
│       ├── context-budget-report.sh
│       ├── validate_execution.sh      # ⊕T1: catches drift in EXECUTION.md
│       └── replay_session.sh          # ⊕T1: reconstruct context from events.jsonl
│
├── evals/                             # ⊕T1: eval-driven development (Anthropic Jan 2026)
│   ├── README.md                      # which framework (Harbor / Braintrust / Phoenix)
│   ├── tasks/                         # individual eval tasks per capability
│   │   ├── 001-login-flow.task.yaml
│   │   ├── 002-create-project.task.yaml
│   │   └── ...
│   ├── graders/                       # grading logic
│   │   ├── code_based.py              # deterministic asserts
│   │   ├── llm_judge.py               # LLM-based rubric grading
│   │   └── human_review_template.md
│   ├── trials/                        # multiple attempts per task (non-determinism)
│   ├── transcripts/                   # complete records (read regularly!)
│   ├── outcomes/                      # final environmental states
│   └── reports/                       # pass@k and pass^k summaries
│
├── work/                              # ★ THE BRIDGE — orchestrator writes, workers read
│   ├── TASK_TEMPLATE.md
│   ├── REPORT_TEMPLATE.md
│   ├── WORKER_PROMPT.md
│   ├── wave-1/  wave-2/  wave-N/      # task files per wave
│   └── reports/wave-1/  wave-2/       # worker reports
│
├── workflows/                         # ⊕T2: declarative workflow definitions (JSON)
│   ├── bug_fix.json
│   ├── new_feature.json
│   ├── data_extraction.json
│   └── (per project)
│
├── .specify/                          # Spec-driven (Spec-Kit + Kiro)
│   ├── memory/
│   │   └── constitution.md
│   ├── steering.md
│   └── specs/wave-N/
│       ├── spec.md  plan.md  tasks.md  contracts/
│
├── plan/                              # 3 LIVING strategic docs (high-level)
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── EXECUTION.md                   # ⊕ tracks git commit hashes per shipped wave
│
├── docs/                              # ★ EXPANDED with subcategories
│   ├── waves/                         # per-wave briefs + per-wave gotchas
│   │   ├── wave-N-brief.md
│   │   └── wave-N-gotchas.md          # ⊕T1: captured DURING, not after
│   ├── decisions/                     # ADRs
│   ├── historical/                    # superseded
│   ├── architecture/                  # ⊕T2: subsystem-by-subsystem detail
│   ├── flows/                         # ⊕T2: data/state/user flow diagrams + descriptions
│   ├── schemas/                       # ⊕T2: data schemas, ERD, OpenAPI
│   ├── agents/                        # ⊕T2: sub-agent docs FOR external readers
│   ├── operational/                   # ⊕T2: ops manuals
│   │   ├── OBSERVABILITY.md
│   │   ├── PERFORMANCE_SLOS.md
│   │   ├── INCIDENT_RESPONSE_PLAYBOOK.md
│   │   ├── PRODUCTION_WALKTHROUGH.md
│   │   ├── SECURITY_PERIMETER_GUIDE.md
│   │   └── DATA_INTAKE_PROTOCOL.md
│   ├── audits/                        # ⊕T2: date-stamped periodic reports
│   │   ├── YYYY-MM-DD-final-audit.md
│   │   ├── YYYY-MM-DD-production-readiness.md
│   │   ├── YYYY-MM-DD-docs-sync-issues.md
│   │   ├── YYYY-MM-DD-tech-debt-inventory.md
│   │   └── YYYY-MM-DD-security-audit.md
│   ├── compliance/                    # ⊕T3: regulatory docs
│   │   ├── DPDP_COMPLIANCE.md         # India Digital Personal Data Protection
│   │   ├── GDPR_COMPLIANCE.md         # EU
│   │   ├── HIPAA_COMPLIANCE.md        # US healthcare
│   │   ├── SOC2_NOTES.md
│   │   └── certificates/              # PDFs of issued certificates
│   ├── benchmarks/                    # ⊕T2: perf benchmarks + results
│   ├── business/                      # ⊕T4: stakeholder/customer-facing
│   │   ├── STAKEHOLDER_UPDATE.md
│   │   ├── demo_video_script.md
│   │   └── pricing.md
│   ├── runtime/                       # ⊕T2: runtime configs, env vars catalog
│   ├── runbook.md                     # operational guide
│   ├── conventions.md
│   ├── conflict_resolution.md
│   ├── deployment.md
│   ├── SCOPE_GUARD.md
│   ├── api.md
│   ├── interview_runbook.md           # ⊕T1: formal user-interview process
│   └── REPOSITORY_STRUCTURE_AND_CLEANUP_PLAN.md  # ⊕T2: meta-doc for repo health
│
├── prompts/                           # ★ EVOLVING prompts
│   ├── current/                       # actively used worker prompts
│   ├── archive/                       # superseded
│   ├── hybrid/                        # ⊕T2: experimental combinations
│   ├── wave-2/  wave-N/               # wave-scoped overrides
│   ├── INDEX.md                       # ⊕T1: navigation index
│   └── EXAMPLE_FILLED_TASK.md         # ⊕T1: worked example
│
├── attic/                             # ★ ARCHIVE — superseded work, never deleted
│
├── deliverables/                      # ⊕T4: MULTI-OUTPUT
│   ├── paper/  patent/  report/  slides/  demo/
│
├── src/                               # actual code (workers write here)
│   └── (per-domain modules)
│
├── tests/                             # ★ EXPANDED TAXONOMY
│   ├── unit/  integration/  e2e/  golden/  fuzz/  performance/  security/
│
├── data/                              # ⊕ if data-heavy
│   ├── raw/  samples/  synthetic/  annotations/  gold/  ontology/
│
├── corpus/                            # ⊕ if domain-corpus-heavy (NLP/research)
├── evidence/                          # ⊕ if research/eval-heavy
│
├── models/                            # ⊕ if ML — versioned
│   ├── <name>-v1/  <name>-v2/  <name>-final/
│
├── schema/                            # JSON Schema / Pydantic
│   └── db_struct.sql                  # ⊕T2: explicit DB structure snapshot
├── config/
├── scripts/
├── ui/                                # if has UI
├── deployment/                        # IaC, k8s manifests
├── resources/                         # reference materials
├── logs/
├── results/
│
├── mcp.json                           # MCP server declarations
├── skills.manifest.json               # ⊕T1: desired skill versions
├── skills-lock.json                   # ⊕T1: pinned skill versions (lockfile)
├── architecture.png                   # ⊕T2: visual diagram (PlantUML/Mermaid output)
├── Makefile
├── Dockerfile                         # default backend
├── Dockerfile.api                     # ⊕T3: when multi-service split
├── Dockerfile.frontend                # ⊕T3
├── Dockerfile.nginx                   # ⊕T3: reverse proxy
├── Dockerfile.orchestration           # ⊕T3: background workers
├── Dockerfile.sandbox                 # ⊕T3: worker code execution sandbox
├── docker-compose.yml                 # default
├── docker-compose.dev.yml             # ⊕T2: dev overrides (hot reload, debug)
├── docker-compose.prod.yml            # ⊕T3: prod overrides (replicas, secrets)
├── Procfile                           # ⊕T4: process manifest (Heroku/Railway/Fly)
├── prometheus.yml                     # ⊕T2: observability config
├── pyproject.toml                     # Python config
├── pytest.ini                         # ⊕T2: standalone pytest config (some tools prefer this)
├── requirements.txt
├── .pre-commit-config.yaml
├── .env.example
├── .gitignore
├── .dockerignore
└── .github/
    └── workflows/
        ├── ci.yml                     # T1: lint + test + acceptance
        ├── test.yml                   # T1: matrix tests
        ├── security.yml               # T1: pip-audit + npm-audit + secrets
        ├── perf_regression.yml        # ⊕T2: perf budget enforcement
        ├── docs_sync.yml              # ⊕T2: detect docs/code drift
        ├── audit.yml                  # ⊕T3: periodic compliance audit
        └── train_on_data.yml          # if ML — model training pipeline
```

**Marker key:** `★` = always; `⊕T1/T2/T3/T4` = add at this tier.

---

## 3. Adaptation Mechanism

When you paste this file + your brief, the orchestrator:

### 3.1 — Variable extraction

| Variable | Source | Example |
|---|---|---|
| `{{PROJECT_NAME}}` | Brief title / domain | `rfq-to-boq`, `swa-erp` |
| `{{PROJECT_GOAL}}` | One-line from brief | "Convert RFQ PDFs to structured BOQ" |
| `{{DOMAIN}}` | Inferred | NLP / web / data pipeline / ML / ERP |
| `{{TECH_STACK}}` | Inferred + asked | Python+FastAPI+React or Node+NestJS |
| `{{TIER}}` | Asked (default T1) | T1 / T2 / T3 / T4 |
| `{{MVP_DEFINITION}}` | First wave scope | "Ingest one PDF, output one BOQ row" |
| `{{WAVES}}` | Decomposition | 4–8 waves with dependency graph |
| `{{ENTITIES}}` | Domain model | Material / Quantity / Standard |
| `{{SUCCESS_METRICS}}` | Acceptance | F1 ≥ 0.85, <60s, etc. |
| `{{RISKS}}` | Risk register | OCR noise, scope omission |
| `{{MCP_SERVERS}}` | Domain-relevant | playwright / serena / tavily / context7 |
| `{{COMPLIANCE}}` | Regulatory | DPDP / GDPR / HIPAA / none |
| `{{HAS_*}}` flags | Inferred | MODELS / UI / DELIVERABLES / DATA / CORPUS / EVIDENCE |

### 3.2 — Generation order

1. Create folder structure for chosen tier
2. Write `plan/{PRD,ARCHITECTURE,EXECUTION}.md`
3. Write `.specify/memory/constitution.md`
4. For each wave: `.specify/specs/wave-N/{spec,plan,tasks,contracts}`
5. Root: `CLAUDE.md`, `KIMI.md`, `HANDOFF.md`, `HIERARCHY.md`, `README.md`, `HOW_TO_RUN.md`, `CHANGELOG.md`, `CONTRIBUTING.md`
6. Tier additions:
   - **T2:** `BACKLOG.md`, `HALL_OF_SHAME.md`, `docs/operational/`, `docs/audits/<today>/`, `prometheus.yml`, `docker-compose.dev.yml`, `pytest.ini`, `skills.manifest.json` + `skills-lock.json`, validators
   - **T3:** `docs/compliance/`, multi-Dockerfile split, `docker-compose.prod.yml`, `audit.yml` workflow, `db_struct.sql`
   - **T4:** `ROADMAP.md`, `STARTUP_ROADMAP.md`, `docs/business/`, `Procfile`, `deliverables/`, demo script
7. Orchestrator apparatus: ROLE, core, commands, skills, agents, hooks, recipes, rules, memory, scripts
8. Wave-1 task files in `work/wave-1/`
9. `mcp.json`, `Makefile`, language configs, CI workflows, `.gitignore`, `.env.example`
10. Print: "Setup complete. Open OpenCode CLI windows and paste work/wave-1/01-*.md."

### 3.3 — Ongoing operations

- New wave → `/plan wave-N` regenerates specs
- New task → `/dispatch` produces briefs
- Decision → ADR in `docs/decisions/`
- Failure pattern → entry in `HALL_OF_SHAME.md`
- Wave gotcha → `docs/waves/wave-N-gotchas.md` updated DURING the wave
- Periodic (T2+): `/audit` produces `docs/audits/<today>-*.md`
- Old patterns → `attic/`, `docs/historical/`, `prompts/archive/` — never deleted

---

## 4. Templates (NEW IN v1.2)

### 4.1 — `HALL_OF_SHAME.md` (⊕T2 — failure archive)

```markdown
# Hall of Shame — Failure Pattern Archive

> Records failure patterns so they are never repeated.
> Learning tool, not blame tool.

## Pattern N: <descriptive title>

- **Date:** YYYY-MM-DD
- **Test / Component:** path/to/file.py · `test_name`
- **Severity:** Critical | High | Medium | Low
- **Root cause:** what actually went wrong (one paragraph)
- **Impact:** what broke for users / what slipped past tests
- **Fix:** what was changed (file + line refs + commit hash)
- **Prevention:** new test / lint rule / convention / ADR that stops this from recurring
```

**Why it works:** worker who hits a similar bug greps for it and finds the prior fix. Orchestrator's `self-evolve` skill scans this file before dispatching new tasks.

### 4.2 — `BACKLOG.md` (⊕T2 — parked ideas)

```markdown
# Backlog

> Parked ideas. NOT scheduled. NOT promised.
> Each item: title · why · rough size · earliest possible wave.
> Move into a wave when capacity allows.

## Features
- [ ] **Multi-currency support** · clients with USD/EUR contracts · M · earliest wave-7
- [ ] **WhatsApp notifications** · field team wants mobile reminders · S · earliest wave-9

## Tech debt
- [ ] **Migrate to async SQLAlchemy** · perf at 10k users · L · earliest wave-10

## Bugs (deferred)
- [ ] **Dashboard cache invalidation lag (~5s)** · acceptable for now · S · earliest wave-8

## Research
- [ ] **Investigate Postgres LISTEN/NOTIFY for live updates** · vs WebSocket · M · earliest wave-9
```

### 4.3 — `docs/waves/wave-N-gotchas.md` (⊕T1 — Hermes-style learning)

```markdown
# Wave N Gotchas

> Captured DURING the wave, not at the end. Workers fill this in as they hit surprises.

## Gotchas

### G-1: Pydantic v2 doesn't accept `Optional[X]` in `model_config(extra="forbid")`
- **Hit by:** task 03 (users API)
- **Workaround:** use `X | None` instead, or relax to `extra="ignore"`
- **Permanent fix needed:** Y — added to `orchestrator/rules/python.md`

### G-2: Alembic autogenerate misses index-only changes
- **Hit by:** task 01
- **Workaround:** manually edit migration after autogenerate
- **Permanent fix needed:** N — known Alembic limitation
```

### 4.4 — `docs/audits/YYYY-MM-DD-final-audit.md` (⊕T2 — periodic audit)

```markdown
# Final Audit — YYYY-MM-DD

## Scope
Wave-N just shipped. This audit verifies acceptance criteria, security, performance, docs sync.

## Findings

### CRITICAL (must fix before next wave)
- (none) ✅

### HIGH (fix in next wave)
- N+1 query in `services/projects.py:list_projects` — add eager loading
- Missing index on `audit_log(entity_type, entity_id)`

### MEDIUM (backlog)
- ...

### LOW (informational)
- ...

## Sign-off
- Orchestrator: ✅
- Verifier sub-agent: ✅
- Human reviewer: <name> · ✅

Next audit: YYYY-MM-DD (after wave-N+1 ships).
```

### 4.5 — `docs/operational/OBSERVABILITY.md` (⊕T2)

```markdown
# Observability

## What we observe
- Logs · structured JSON · stdout · collected by <fluentd|cloudwatch|datadog>
- Metrics · Prometheus · scraped from /metrics · dashboards in Grafana
- Traces · OpenTelemetry · exporter to Jaeger/Tempo
- Errors · Sentry · env-gated

## Service map
<diagram or ASCII>

## Key dashboards
- API latency P50/P95/P99
- Background-job queue depth
- DB connection pool utilization
- Per-endpoint error rate

## Alert thresholds
- P95 latency > 1s for 5min → page
- Error rate > 1% for 5min → page
- Job queue depth > 1000 → warn
- DB pool > 90% for 5min → warn

## Runbook links
See INCIDENT_RESPONSE_PLAYBOOK.md.
```

### 4.6 — `docs/operational/PERFORMANCE_SLOS.md` (⊕T2)

```markdown
# Performance SLOs

| Endpoint / Operation | Target P95 | Acceptable P95 | Minimum P95 |
|---|---|---|---|
| GET /api/projects (list, 100 items) | 100ms | 300ms | 500ms |
| POST /api/auth/login | 200ms | 500ms | 1s |
| BOQ upload + parse (100 lines) | 30s | 60s | 120s |

## Enforcement
- CI runs `tests/performance/` against staging snapshot
- Builds fail if P95 exceeds Minimum
- Weekly report comparing to Target/Acceptable
```

### 4.7 — `docs/operational/INCIDENT_RESPONSE_PLAYBOOK.md` (⊕T2)

```markdown
# Incident Response Playbook

## Severity definitions
- SEV-1: Service down or data loss
- SEV-2: Major feature broken, no workaround
- SEV-3: Minor feature broken, workaround exists
- SEV-4: Cosmetic / docs

## On-call rotation
See <PagerDuty / OpsGenie / rotation doc>.

## Response steps
1. Acknowledge within 5 min
2. Assess severity
3. Stabilize (rollback if recent deploy)
4. Communicate (status page + Slack)
5. Resolve
6. Post-mortem within 48h → entry in HALL_OF_SHAME.md

## Common scenarios
- DB primary down → fail over to replica (steps...)
- Worker queue stuck → restart Celery (steps...)
- JWT secret leaked → rotate + revoke all refresh tokens (steps...)
```

### 4.8 — `STAKEHOLDER_UPDATE.md` (⊕T4 — periodic external comm)

```markdown
# Stakeholder Update — Week of YYYY-MM-DD

## What shipped
- ...

## What's next (this/next week)
- ...

## Risks I want you to see
- ...

## Asks (decisions I need from you)
- [ ] ...

## Metrics
- Users active this week: N
- Top feature usage: ...
- Error rate: ...
```

### 4.9 — `STARTUP_ROADMAP.md` (⊕T4)

```markdown
# Startup Roadmap

## Vision (1-year)
What does success look like 12 months from now?

## ICP (Ideal Customer Profile)
- Who exactly are we building for?
- Where do they live online?
- What do they pay for now?

## GTM (Go-To-Market)
- How do we reach the first 10 customers?
- The next 100?
- The next 1000?

## Pricing experiments
| Experiment | Hypothesis | Outcome | Decision |
|---|---|---|---|
| ... | ... | ... | ... |

## Roadmap (quarter granularity)
- Q1: <theme>
- Q2: <theme>
- Q3: <theme>
- Q4: <theme>

## Inflection points (when to pivot)
- If <metric> < <threshold> by <date>, pivot to <plan B>
```

### 4.10 — `skills.manifest.json` + `skills-lock.json` (⊕T1)

**Manifest** (desired):
```json
{
  "$schema": "https://agentskills.io/schemas/manifest.v1.json",
  "skills": {
    "tdd": "^1.2.0",
    "code-review": "^2.0.0",
    "pdf-processing": "^1.5.0",
    "fastapi-patterns": "^1.0.0",
    "sqlalchemy-orm": "^2.0.0"
  }
}
```

**Lock** (resolved + checksums):
```json
{
  "$schema": "https://agentskills.io/schemas/lock.v1.json",
  "skills": [
    {
      "name": "tdd",
      "version": "1.2.4",
      "source": "agentskills.io/skills/tdd",
      "sha256": "abc123...",
      "files": ["SKILL.md", "references/red-green-refactor.md"]
    }
  ]
}
```

**Why:** reproducible builds. New developer installs same skills the orchestrator used.

### 4.11 — `workflows/<name>.json` (⊕T2 — declarative workflow)

```json
{
  "$schema": "https://os-setup.io/schemas/workflow.v1.json",
  "name": "bug_fix",
  "description": "Reproduce → fix → verify → merge a bug",
  "steps": [
    {
      "id": "reproduce",
      "agent": "codebase-explorer",
      "input": {"bug_report": "$INPUT"},
      "output": "reproduction_steps.md"
    },
    {
      "id": "write_failing_test",
      "skill": "tdd",
      "depends_on": ["reproduce"]
    },
    {
      "id": "fix",
      "depends_on": ["write_failing_test"]
    },
    {
      "id": "verify",
      "agent": "verifier",
      "depends_on": ["fix"]
    },
    {
      "id": "merge",
      "command": "/merge",
      "depends_on": ["verify"]
    }
  ],
  "state_file": "orchestrator/memory/states/bug_fix-state.json"
}
```

Per-workflow state JSONs in `orchestrator/memory/states/` track current step, outputs, retries.

### 4.12 — `EXECUTION.md` row format (refined in v1.2)

```markdown
| Wave | Name | Status | Tasks | Commit | Notes |
|---|---|---|---|---|---|
| 1 | Foundation | **SHIPPED** ✅ | 5/5 | `df1b779` | wave-1-complete tag |
| 2 | Clients + Projects | **SHIPPED** ✅ | 5/5 | `d1e3017` | 52 tests pass |
| 3 | Quotation/BOQ | **READY TO DISPATCH** | 0/5 | — | spec + task files ready |
| 4 | Tasks | pending | — | — | depends on wave-2 |
```

**One row per wave. Status drift validator catches duplicates.**

### 4.13 — `orchestrator/scripts/validate_execution.sh` (⊕T1)

```bash
#!/bin/bash
# Catches drift in plan/EXECUTION.md
set -e
cd "$(dirname "$0")/../.."

# 1. No duplicate wave numbers in status table
DUPS=$(awk '/^\| [0-9]+ \|/ {print $2}' plan/EXECUTION.md | sort | uniq -d)
if [ -n "$DUPS" ]; then
  echo "DRIFT: duplicate wave numbers in EXECUTION.md: $DUPS"
  exit 1
fi

# 2. Active wave matches HANDOFF.md
EXEC_ACTIVE=$(grep -A0 "^\*\*Active wave:\*\*" plan/EXECUTION.md | head -1)
HANDOFF_ACTIVE=$(grep -A0 "^- Active wave:" HANDOFF.md | head -1)
if [ -n "$EXEC_ACTIVE" ] && [ -n "$HANDOFF_ACTIVE" ]; then
  WE=$(echo "$EXEC_ACTIVE" | grep -oE "wave-[0-9]+")
  WH=$(echo "$HANDOFF_ACTIVE" | grep -oE "wave-[0-9]+")
  if [ "$WE" != "$WH" ]; then
    echo "DRIFT: EXECUTION.md says active=$WE but HANDOFF.md says active=$WH"
    exit 1
  fi
fi

# 3. Every "SHIPPED" wave has a commit hash
SHIPPED_NO_HASH=$(awk '/SHIPPED.*\| —/' plan/EXECUTION.md)
if [ -n "$SHIPPED_NO_HASH" ]; then
  echo "DRIFT: shipped wave with no commit hash:"
  echo "$SHIPPED_NO_HASH"
  exit 1
fi

echo "EXECUTION.md is clean"
```

Run in CI via `docs_sync.yml`. Run after every `/merge`.

### 4.14 — `docs/REPOSITORY_STRUCTURE_AND_CLEANUP_PLAN.md` (⊕T2 — meta-doc)

```markdown
# Repository Structure + Cleanup Plan

## Last audit: YYYY-MM-DD

## Current state
- Total files: N
- Top-level files: M (target: under 25)
- attic/ size: P MB (review if >100MB)
- prompts/archive/ count: Q (review if >50)

## Cleanup targets
- [ ] Move <list> from root to docs/operational/
- [ ] Consolidate <list> in attic/
- [ ] Delete <obviously dead> (with caution — confirm first)

## Folder ownership recap
| Folder | Owner | Last reviewed |
|---|---|---|

## Drift indicators
- Files referenced in CLAUDE.md but missing: <list>
- Files in src/ not imported by anything: <list>
- ADRs older than 1 year with no update: <list>

## Next audit due: YYYY-MM-DD
```

Generated by `/audit` periodically (T2+).

### 4.15 — `docs/interview_runbook.md` (⊕T1)

```markdown
# Interview Runbook

## When to interview the user
- New feature request (before /plan)
- Ambiguity in spec (before /dispatch)
- Worker REVISE for the 2nd time on same task
- Scope question
- Tech choice with multiple valid paths

## How to interview
1. Use the `interviewer` sub-agent
2. Frame as MULTIPLE CHOICE wherever possible
3. Max 4 questions per interview
4. Mark recommended option (with reason)
5. Capture answer + reasoning in ADR

## Questions NOT to ask
- "Any thoughts?" (too open)
- "Should we do X?" without alternatives
- Questions answerable by reading PRD/ARCHITECTURE

## Example: clarifying a vague requirement
Bad: "How should the dashboard work?"
Good: "Dashboard cards: real-time (refresh every 10s) / on-pull (refresh on user action) / cached (refresh hourly)?"
```

### 4.16 — Multi-Dockerfile pattern (⊕T3)

```dockerfile
# Dockerfile.api — backend FastAPI service
FROM python:3.11-slim AS builder
# ... (as before, just one service)
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile.orchestration — Celery workers
FROM python:3.11-slim AS builder
# ... (shares deps with .api but different CMD)
CMD ["celery", "-A", "src.backend.workers.celery_app", "worker", "--loglevel=info"]

# Dockerfile.nginx — reverse proxy + static
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Dockerfile.sandbox — worker code-execution sandbox
FROM python:3.11-slim
# Locked-down: no network, /tmp scratch, capped memory
USER nobody:nogroup
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /sandbox
CMD ["python3", "-c", "print('sandbox ready')"]
```

### 4.17 — env-specific docker-compose (⊕T2)

```yaml
# docker-compose.yml — defaults (single source for service definitions)
services:
  backend:
    build: { context: ., dockerfile: Dockerfile.api }
    environment:
      DATABASE_URL: postgresql://swa:swa@postgres:5432/swa_erp
  # ...

# docker-compose.dev.yml — overrides for dev (hot reload, debug)
services:
  backend:
    volumes:
      - ./src/backend:/app/src/backend  # hot reload
    environment:
      DEBUG: "true"
      DATABASE_URL: postgresql://swa:swa@postgres:5432/swa_erp_dev
    ports:
      - "5678:5678"  # debugpy
    command: ["uvicorn", "src.backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.prod.yml — overrides for prod (replicas, secrets, healthchecks)
services:
  backend:
    deploy:
      replicas: 3
      restart_policy: { condition: on-failure }
    environment:
      DATABASE_URL_FILE: /run/secrets/database_url
    secrets:
      - database_url
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
secrets:
  database_url:
    file: ./secrets/database_url
```

**Run:**
- Dev: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`
- Prod: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`

### 4.18 — `Procfile` (⊕T4)

```
web: uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT
worker: celery -A src.backend.workers.celery_app worker --loglevel=info
beat: celery -A src.backend.workers.celery_app beat
release: cd src/backend && alembic upgrade head
```

Works on Heroku, Railway, Fly.io, Render, DigitalOcean App Platform.

### 4.19 — `prometheus.yml` (⊕T2)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'swa-erp-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'swa-erp-workers'
    static_configs:
      - targets: ['orchestration:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 4.20 — `architecture.png` (⊕T2 — visual diagram)

Generated from Mermaid or PlantUML source kept at `docs/architecture/architecture.mmd`. CI re-renders PNG on commit.

Example `architecture.mmd`:
```mermaid
graph TB
  Browser --> Nginx[Nginx reverse proxy]
  Nginx --> API[FastAPI service]
  API --> DB[(PostgreSQL)]
  API --> Redis[(Redis)]
  Redis --> Workers[Celery workers]
  Workers --> DB
  Workers --> Storage[S3 / MinIO]
```

CI: `mmdc -i docs/architecture/architecture.mmd -o architecture.png`

### 4.21 — Carry-forward templates from v1.1

(Unchanged from v1.1 — still required: `CLAUDE.md` kernel, `HANDOFF.md`, `HIERARCHY.md`, `TASK_TEMPLATE.md`, `REPORT_TEMPLATE.md`, `WORKER_PROMPT.md`, `Makefile`, `mcp.json`, `pyproject.toml`, `.pre-commit-config.yaml`, CI workflows.)

### 4.22 — Skills/Commands Unification (Anthropic 2026, NEW in v1.3)

Per the May 2026 Claude Code Skills docs: **custom commands have been merged into skills**. Both forms below create `/deploy` and work identically:

```
# Form A — command (legacy alias, still works)
.claude/commands/deploy.md

# Form B — skill (preferred; supports directory + resources)
.claude/skills/deploy/SKILL.md
.claude/skills/deploy/references/checklist.md
.claude/skills/deploy/scripts/rollback.sh
```

**Skill frontmatter (canonical 2026 schema):**

```yaml
---
name: deploy
description: Deploy the application to prod. Runs migrations, smoke tests, opens PR.
allowed-tools: Bash(git:*) Bash(make:*) Read Write    # ⊕T2: pre-approve tool surface
invocation: claude                                     # claude | user | both
subagent: true                                         # run in isolated context (T2+)
license: MIT
metadata:
  author: swa-erp
  version: "1.0.3"
---

# Deploy

When to use this skill: ...
```

**Three new fields formalized in 2026:**
1. **`allowed-tools`** — space-separated tools the skill may call. Tighter than session-wide permissions.
2. **`invocation`** — who can invoke. `claude` = only Claude decides; `user` = only `/deploy`; `both`.
3. **`subagent: true`** — load the skill in a sub-agent context (separate context window). Use for read-heavy or risky skills.

**Our default:** `orchestrator/skills/*/SKILL.md` files use this schema. `orchestrator/commands/*.md` (legacy) are deprecated synonyms kept for backwards compat — new entries should be skills.

### 4.23 — `evals/tasks/<NNN>-<name>.task.yaml` template (⊕T1 — Anthropic Jan 2026)

```yaml
---
id: 001-login-flow
description: Admin can log in and reach dashboard
type: e2e                # unit | integration | e2e | conversational | research | computer-use
capability: auth         # which capability this evaluates
---

# Eval Task: 001-login-flow

## Input
- App in clean state (fresh DB seeded with admin@swa.local / admin123!)
- User opens browser to http://localhost:3000

## Agent execution
What the agent (worker / orchestrator) must do:
1. Navigate to /login
2. Enter credentials
3. Submit
4. Land on /dashboard

## Outcome verification (what counts as success)
- DOM check: page URL ends with /dashboard
- DOM check: text "Welcome" visible
- Session state: access_token in localStorage
- Audit log row exists: action=auth.login_success

## Grader
- Type: code-based (deterministic)
- File: evals/graders/code_based.py::test_login_flow

## Trials
- k: 5 (run 5 times to measure non-determinism)
- Report pass@5 and pass^5

## Anti-patterns to avoid (per Anthropic Jan 2026)
- Don't grade exact tool-call sequence — grade outcome
- Don't reject 96.124 when expecting 96.12 (numerical tolerance)
- Don't share state between trials (each trial fresh)
- Don't let agent bypass (e.g., editing DB directly to "pass" the test)

## Lifecycle stage
- early | growth | regression | production
```

### 4.24 — `evals/README.md` template

```markdown
# Evals — Eval-Driven Development

Per Anthropic Jan 2026 "Demystifying evals for AI agents."

## Philosophy
Capability defined by tests BEFORE the agent can fulfill it. Tests evolve from "can we?" (capability evals) into regression suites as the agent matures.

## Framework
We use: **Harbor** (containerized, Terminal-Bench 2.0 compatible) for backend.
Optional: **Braintrust** (production observability) when we have real users.
Optional: **Phoenix** (open-source tracing) for self-hosted.

## Metrics
- **pass@k** — probability of success in at least 1 of k attempts (capability)
- **pass^k** — probability ALL k attempts succeed (production reliability)

We target:
| Stage | pass@k | pass^k |
|---|---|---|
| Capability eval | 50%+ at k=5 | — |
| Regression suite | 95%+ at k=3 | 80%+ at k=3 |
| Production blocker | — | 99%+ at k=10 |

## Workflow
1. **Build:** convert real failures (from HALL_OF_SHAME.md) + support tickets into 20–50 tasks
2. **Run:** `make evals` or `make eval task=001`
3. **Read transcripts** — DON'T trust scores at face value
4. **Calibrate** LLM-graders against human judgment quarterly
5. **Promote** capability evals → regression suite as pass@k hits 95%+
6. **Maintain** like unit tests — encourage cross-functional contribution

## Anti-patterns (avoid these)
1. Brittle grading (over-specifying numerical precision or tool sequence)
2. Ambiguous task specs (agent can't reasonably complete)
3. Class imbalance (only positive cases, never "agent should refuse")
4. Shared state pollution between trials
5. Bypasses (agent cheats without solving)
6. Saturation (100% pass rate = no signal; add harder tasks)

## When pass^k hits 0%
"Frontier models reaching 0% pass^k usually signal a broken task, not an incapable agent."
Read the transcripts. Fix the task spec.

## Swiss Cheese Model
No single layer catches everything. Combine:
- Capability evals (pre-production)
- Regression suite (every commit)
- Production monitoring (live metrics)
- A/B tests (when applicable)
- User feedback (forms, support)
- Transcript review (weekly)
```

### 4.25 — `orchestrator/memory/session/<wave>-<task>.events.jsonl` format (⊕T1 — durable session log)

Append-only newline-delimited JSON. One event per line:

```jsonl
{"ts": "2026-05-19T03:45:12Z", "id": "evt-001", "type": "task.dispatched", "wave": "wave-1", "task": "01-backend-skeleton", "file": "work/wave-1/01-backend-skeleton.md"}
{"ts": "2026-05-19T04:12:33Z", "id": "evt-002", "type": "worker.started", "task": "01-backend-skeleton", "worker": "opencode-cli-window-1"}
{"ts": "2026-05-19T04:58:01Z", "id": "evt-003", "type": "report.received", "task": "01-backend-skeleton", "file": "work/reports/wave-1/01-backend-skeleton.report.md", "result": "DONE"}
{"ts": "2026-05-19T04:59:44Z", "id": "evt-004", "type": "acceptance.run", "task": "01-backend-skeleton", "cmd": "pytest tests/wave-1/test_skeleton.py -v", "exit_code": 0}
{"ts": "2026-05-19T05:00:12Z", "id": "evt-005", "type": "review.decision", "task": "01-backend-skeleton", "decision": "APPROVE"}
{"ts": "2026-05-19T05:01:33Z", "id": "evt-006", "type": "merge.complete", "task": "01-backend-skeleton", "commit": "abc1234"}
```

**Why JSONL not JSON:** append-only, no rewriting on crash, streaming-friendly. Matches Anthropic's `emitEvent` primitive.

**`replay_session.sh`** reconstructs minimal context for a `wake()` resume by reading the last N events.

### 4.26 — `orchestrator/core/blast-radius.md` (⊕T2 — Anthropic containment)

```markdown
# Blast Radius

Per "How we contain Claude across products." Every action has a blast radius — the worst case if it goes wrong.

## Tier the blast radius
| Radius | Examples | Containment |
|---|---|---|
| **r0 — Read-only** | Read files, grep, list | None needed |
| **r1 — Local repo** | Write to src/, run tests | Auto allowed; git protects |
| **r2 — Local services** | Apply DB migration to dev | Confirm; reversible |
| **r3 — Remote services** | Push to GitHub, send Slack | Confirm; possibly reversible |
| **r4 — External humans** | Email customers, file Jira tickets | Always confirm; HARD to reverse |
| **r5 — Money or data loss** | Charge card, drop prod table | Block by default |

## Mapping to risk tiering
Blast radius **r3+** ⇒ governance tier **T2 (await approval)** minimum.
Blast radius **r5** ⇒ governance tier **T3 (block)** always.

## Auto mode (Anthropic Mar 2026)
Auto mode skips permission prompts for **r0/r1 only**. r2+ always pauses for confirmation, even in auto mode.

## Implementation
- `orchestrator/hooks/pre-tool-use.sh` looks up blast radius of the tool call
- Records radius in session events.jsonl
- Pauses or blocks per tier
```

### 4.27 — Bundled skills (Anthropic 2026)

Claude Code ships bundled skills that work without us defining them:
- `/help` — built-in help
- `/compact` — built-in compaction
- `/debug` — built-in debug helper
- `/code-review` — built-in code review

We don't need to redefine these. We define skills that are **specific to this project** (e.g., `/ship`, `/dispatch`, `/audit`, `/operator`).

---

## 5. Workflow Loops

### 5.1 — Wave lifecycle (unchanged)

```
PRD → /plan wave-N → .specify/specs/wave-N/{spec,plan,tasks,contracts}
    → /dispatch wave-N → work/wave-N/0X-task.md (parallel)
    → workers execute → work/reports/wave-N/0X.report.md
    → /review → APPROVE: /merge | REVISE: rewrite | REJECT: /rollback → attic/
    → (loop until all merged)
    → /ship → final tests + PR + EXECUTION.md (commit hash) + CHANGELOG bumped
    → next wave
```

### 5.2 — NEW: Failure-capture loop (T2+)

```
Bug found → /diagnose → write failing test → fix
         → entry in HALL_OF_SHAME.md (Pattern · Root Cause · Fix · Prevention)
         → if pattern likely to recur: add lint rule / convention to orchestrator/rules/
         → if test gap: add to tests/golden/ or tests/fuzz/
```

### 5.3 — NEW: Audit cycle (T2+)

```
End of each wave → /audit
                → docs/audits/<today>-final-audit.md
                → if CRITICAL findings: block ship
                → if HIGH: add tasks to next wave
                → if MEDIUM: add to BACKLOG.md

Monthly       → /audit --type=docs-sync
              → docs/audits/<today>-docs-sync-issues.md
              → fix drift

Quarterly     → /audit --type=tech-debt
              → docs/audits/<today>-tech-debt-inventory.md
              → /audit --type=security
              → docs/audits/<today>-security-audit.md
```

### 5.4 — NEW: Stakeholder cadence (T4)

```
Weekly       → STAKEHOLDER_UPDATE.md (what shipped, what's next, risks, asks)
Monthly      → /reflect on the month → retrospective ADR
Quarterly    → STARTUP_ROADMAP.md updated (vision, ICP, GTM, pricing)
```

### 5.5 — NEW v1.3: Eval-driven development loop (T1+, Anthropic Jan 2026)

```
New capability requested
    ↓
Write 5–20 eval TASKS first (evals/tasks/NNN-*.task.yaml)
    ↓
Run evals → pass@k = 0% (expected — agent can't do this yet)
    ↓
/plan wave → /dispatch → workers implement
    ↓
Re-run evals → pass@k climbs
    ↓
When pass@k ≥ 50% at k=5 → capability eval graduates to regression suite
    ↓
Every commit re-runs regression suite
    ↓
When pass@k saturates at 100% → add harder tasks (no signal otherwise)
    ↓
Read transcripts weekly → calibrate LLM-graders quarterly
```

### 5.6 — NEW v1.3: wake() resume loop (after crash or context switch)

```
Orchestrator session ends or crashes
    ↓
Open Claude Code (or Kimi) in same directory
    ↓
Auto-loads: CLAUDE.md (kernel) + HANDOFF.md (current state)
    ↓
Read most recent events from orchestrator/memory/session/<wave>-<task>.events.jsonl
    ↓
Run: bash orchestrator/scripts/replay_session.sh <wave> <task>
    → Outputs: "Last 5 events: ... ; In progress: <task>; Pending review: <list>"
    ↓
Resume from exactly that point
```

### 5.7 — NEW v1.3: Auto mode (Anthropic Mar 2026)

```
Routine task (e.g., format, lint, regen requirements) at blast radius r0/r1
    ↓
Enable auto mode: claude --auto OR /auto-mode on
    ↓
Orchestrator skips permission prompts for r0/r1 actions
    ↓
r2+ actions still pause for confirmation
    ↓
Logged to session events.jsonl with autoMode=true
    ↓
Disable when done: /auto-mode off
```

---

## 6. Quality Gates

### 6.1 — Risk tiering (T0–T3, unchanged)

| Tier | Examples | Gate |
|---|---|---|
| T0 — Auto | Read files, run tests, lint | Execute immediately |
| T1 — Log + proceed | Write to src/, modify tests | Log to MEMORY.md, proceed |
| T2 — Await approval | Add deps, change CI, modify migrations | Pause, ask human |
| T3 — Block | rm -rf, force-push, drop tables | Block unconditionally |

### 6.2 — MCP security gate
Unchanged from v1.1. `orchestrator/hooks/mcp-security-gate.sh` validates calls against `mcp.json` whitelist.

### 6.3 — Acceptance verification
Boris's #1 rule: orchestrator runs acceptance commands before approving.

### 6.4 — CI enforcement
- `ci.yml`: lint + test + acceptance per push
- `test.yml`: matrix
- `security.yml`: pip-audit + npm-audit + secrets scan
- `perf_regression.yml` (⊕T2): perf budgets
- `docs_sync.yml` (⊕T2): runs `validate_execution.sh` + drift detection
- `audit.yml` (⊕T3): periodic compliance audit

### 6.5 — Evolution discipline (unchanged)
Never delete. Move to `attic/`, `docs/historical/`, `prompts/archive/`.

### 6.6 — NEW: Drift detection (T2+)

- Files referenced in `CLAUDE.md` must exist (validator)
- Files in `src/` not imported by any other file are candidates for `attic/`
- ADRs not touched in 1 year get an "is this still current?" check
- `validate_execution.sh` runs in CI

### 6.7 — NEW: Failure→Prevention loop (T2+)

Every CRITICAL bug from `/audit` or production incident MUST result in:
1. Entry in `HALL_OF_SHAME.md`
2. New test (regression)
3. New eval task in `evals/tasks/`
4. New rule / convention / ADR (prevention)

### 6.8 — NEW v1.3: Swiss Cheese verification (Anthropic Jan 2026)

No single verification layer catches everything. Stack them:

| Layer | What it catches | When it runs |
|---|---|---|
| **Pydantic validation** | Type/shape errors at API boundary | Every request |
| **Lint (ruff/eslint)** | Style + obvious bugs | Pre-commit + CI |
| **Unit tests** | Logic in isolation | Pre-commit + CI |
| **Integration tests** | Module interaction | CI |
| **Acceptance contracts** | Spec → reality | CI + /review |
| **E2E tests (Playwright)** | User-visible flows | CI nightly |
| **Eval tasks (pass@k)** | Capability presence | CI for changed waves |
| **Eval regression suite (pass^k)** | Capability NOT regressed | Every commit |
| **Performance budget** | Latency targets met | Pre-deploy |
| **Verifier sub-agent** | Independent code review | /review |
| **Human transcript review** | Eval grader fairness, agent loopholes | Weekly |
| **Production monitoring** | What we missed | Live |

Workers approach: workers run unit/integration. Orchestrator runs acceptance + evals + verifier. CI runs everything. Humans read transcripts.

### 6.9 — NEW v1.3: Eval anti-patterns (Anthropic Jan 2026)

The orchestrator REJECTS evals that exhibit any of these:

1. **Brittle grading.** Rejecting `96.124` when expecting `96.12` (numerical precision). Hardcoded tool-call sequences.
2. **Ambiguous task specs.** Agent can't reasonably complete given unclear instructions.
3. **Class imbalance.** Only testing when behavior SHOULD occur; never testing refusals or edge non-events.
4. **Shared state pollution.** Trials leak artifacts to next trial. Each trial MUST start fresh.
5. **Overlooked bypasses.** Agent "passes" by editing DB directly, hardcoding answers, or skipping the actual work.
6. **Eval saturation.** Capability evals running at 100% pass — no signal. Add harder tasks.

When pass^k = 0%, the task is probably broken, not the agent. Read transcripts.

### 6.10 — NEW v1.3: Transcript review cadence (T2+)

```
Weekly       → Read 5 random eval transcripts. Check:
               - Did graders judge fairly?
               - Did agent "cheat" without doing real work?
               - Were any successes lucky (would fail next time)?
               - Were failures task-spec problems vs real capability gaps?

Monthly      → Calibrate LLM-graders against human judgment on 20 samples
Quarterly    → Full eval suite review; archive resolved tasks; add new tasks
```

Transcripts live in `evals/transcripts/<task-id>/<trial-n>/transcript.json`.

---

## 7. Multi-Output Deliverables (⊕T4, unchanged)

```
deliverables/
├── paper/  patent/  report/  slides/  demo/
```

Each gets its own wave (e.g., `wave-9-final-report`).

---

## 8. Customization Checklist

When applying OS-Setup to a project, the orchestrator confirms all of:

### T1 (always)
- [ ] `{{PROJECT_NAME}}`, `{{PROJECT_GOAL}}`, `{{DOMAIN}}`, `{{TECH_STACK}}`
- [ ] `{{MVP_DEFINITION}}`, `{{WAVES}}`, `{{ENTITIES}}`, `{{SUCCESS_METRICS}}`, `{{RISKS}}`
- [ ] `{{MCP_SERVERS}}` chosen for domain
- [ ] First wave task files in `work/wave-1/`
- [ ] `skills.manifest.json` + `skills-lock.json`
- [ ] `interview_runbook.md`

### ⊕T2 (production)
- [ ] `BACKLOG.md`, `HALL_OF_SHAME.md` initialized
- [ ] `docs/operational/{OBSERVABILITY,PERFORMANCE_SLOS,INCIDENT_RESPONSE_PLAYBOOK}.md`
- [ ] First audit doc in `docs/audits/<today>-baseline.md`
- [ ] `prometheus.yml` configured
- [ ] `docker-compose.dev.yml` overrides
- [ ] `perf_regression.yml` + `docs_sync.yml` workflows
- [ ] `validate_execution.sh` runs in CI
- [ ] `docs/REPOSITORY_STRUCTURE_AND_CLEANUP_PLAN.md`
- [ ] `architecture.mmd` + generated `architecture.png`

### ⊕T3 (enterprise / compliance)
- [ ] `docs/compliance/` filled with applicable docs
- [ ] Multi-Dockerfile split
- [ ] `docker-compose.prod.yml` overrides
- [ ] `audit.yml` workflow
- [ ] `schema/db_struct.sql`
- [ ] Certificates folder

### ⊕T4 (startup / customer-facing)
- [ ] `ROADMAP.md`, `STARTUP_ROADMAP.md`
- [ ] `docs/business/STAKEHOLDER_UPDATE.md`
- [ ] `docs/business/demo_video_script.md`
- [ ] `Procfile` for platform-agnostic deploy
- [ ] `deliverables/` subfolders relevant to product (e.g., `slides/`)

---

## 9. Open Standards Respected

| Standard | Where it lives |
|---|---|
| agentskills.io | `orchestrator/skills/*/SKILL.md` + `skills.manifest.json` + `skills-lock.json` |
| MCP | `mcp.json` |
| A2A (optional) | when agents from different providers communicate |
| Spec-Kit SDD | `.specify/` |
| Kiro steering | `.specify/steering.md` |
| ADRs | `docs/decisions/` |
| Conventional Commits | enforced via `.pre-commit-config.yaml` |
| Keep a Changelog | `CHANGELOG.md` |
| Semantic Versioning | tagged releases |
| 12-Factor App + Agents | `orchestrator/core/12-factor.md` |
| OpenAPI | `docs/schemas/api.yaml` |
| OpenTelemetry | `docs/operational/OBSERVABILITY.md` |
| Procfile spec | `Procfile` (T4) |

---

## 10. What Each Iteration Contributed

| Iteration | What it added |
|---|---|
| #1 — Basic 3-folder split | plan/docs/prompts |
| #2 — 4 plan docs + specs | spec-driven discipline |
| #3 — Skills primitive | CLAUDE.md auto-loaded, agentskills.io |
| #4 — 12-Factor + 5 patterns + Spec-Kit | governance + canonical patterns |
| #5 — Big fish (SuperClaude + BMAD + kmshihab + commands) | Claude OS pattern, 4-layer apparatus |
| Dedicated #1 — Dual-tier | orchestrator vs workers |
| Dedicated #2 — Simplified | One orchestrator (Claude/Kimi), OpenCode workers, work/ bridge |
| v1.1 — Project 1 lessons | wave terminology, root CLAUDE/HANDOFF/HIERARCHY, attic/, deliverables/, expanded tests/, plural data/, models/ versioning, prompts/wave-N/ |
| v1.2 — Multi-project lessons | Tiers (T0–T4) · HALL_OF_SHAME · BACKLOG · wave gotchas · operational docs (OBSERVABILITY/SLOS/INCIDENT_RESPONSE) · periodic audits · compliance docs · multi-Dockerfile · env-specific docker-compose · Procfile · prometheus · skills-lock · workflows/ + per-workflow state · validate_execution.sh · architecture.png · STAKEHOLDER_UPDATE · STARTUP_ROADMAP · interview_runbook · REPOSITORY_STRUCTURE meta-doc · ROADMAP separation from EXECUTION · EXECUTION row with commit hash · failure→prevention loop |
| **v1.3 — Anthropic 2026 SOTA** | **Brain/Hands/Session triad (Apr 2026) · durable events.jsonl session log · `wake()` resume · skills/commands unification (`allowed-tools` + `invocation` + `subagent`) · `evals/` first-class directory · eval-driven development (pass@k, pass^k) · eval anti-patterns · Swiss Cheese verification · transcript review cadence · auto mode for r0/r1 (Mar 2026) · blast-radius governance (r0–r5) · Harbor/Braintrust/Phoenix framework support · bundled-skills awareness · harness as discrete component · replay_session.sh** |

---

## 11. Final Self-Check Before Using

When the orchestrator finishes generating a project, it confirms (tier-dependent):

### T1 (always)
- [ ] Root: `CLAUDE.md`, `KIMI.md` (identical), `AGENTS.md` (alias), `HANDOFF.md`, `HIERARCHY.md`, `README.md`, `HOW_TO_RUN.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `Makefile`, `mcp.json`, `requirements.txt` (or `package.json`), `pyproject.toml` (Python), `pytest.ini` (if used), `.pre-commit-config.yaml`, `.gitignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `skills.manifest.json`, `skills-lock.json`
- [ ] `.claude/settings.local.json`
- [ ] `orchestrator/`: `ROLE.md`, `core/` (≥9 incl. `blast-radius.md`), `commands/` (≥10, deprecated synonym), `skills/` (≥12 with `allowed-tools` + `invocation` + `subagent` frontmatter), `agents/` (≥4), `hooks/` (≥6), `recipes/` (≥1), `rules/` (per stack), `memory/{MEMORY.md, session/, states/}`, `scripts/` (≥4 incl. `replay_session.sh`)
- [ ] `work/`: `TASK_TEMPLATE.md`, `REPORT_TEMPLATE.md`, `WORKER_PROMPT.md`, `wave-1/` populated, `reports/wave-1/`
- [ ] `evals/`: `README.md`, `tasks/` (≥5 starter tasks), `graders/`, `trials/`, `transcripts/`, `outcomes/`, `reports/`
- [ ] `.specify/memory/constitution.md`, `specs/wave-1/{spec,plan,tasks,contracts}`
- [ ] `plan/{PRD,ARCHITECTURE,EXECUTION}.md` filled (no placeholders)
- [ ] `docs/{decisions,historical,waves}`, `runbook.md`, `conventions.md`, `SCOPE_GUARD.md`, `interview_runbook.md`
- [ ] `prompts/{current,archive}`, `INDEX.md`
- [ ] `attic/` exists (empty)
- [ ] `tests/{unit,integration,e2e,golden,fuzz,performance,security}/`
- [ ] `data/` (if data-heavy), `models/` (if ML), `corpus/` + `evidence/` (if research)
- [ ] `src/` skeleton matches architecture
- [ ] `.github/workflows/`: `ci.yml`, `test.yml`, `security.yml`, `evals.yml` (NEW v1.3)
- [ ] No `{{PLACEHOLDER}}` remains
- [ ] First wave ready to dispatch
- [ ] First session events.jsonl will be created on first `/dispatch`

### ⊕T2 additions
- [ ] `BACKLOG.md`, `HALL_OF_SHAME.md`
- [ ] `docs/operational/`, `docs/audits/<today>-baseline.md`, `docs/architecture/`, `docs/schemas/`, `docs/flows/`, `docs/benchmarks/`, `docs/runtime/`
- [ ] `docs/REPOSITORY_STRUCTURE_AND_CLEANUP_PLAN.md`
- [ ] `prometheus.yml`, `docker-compose.dev.yml`
- [ ] `architecture.png` (generated)
- [ ] `.github/workflows/{perf_regression,docs_sync}.yml`
- [ ] `validate_execution.sh` working
- [ ] `workflows/` declarative JSONs (if applicable)
- [ ] `orchestrator/memory/states/` (per-workflow state files)
- [ ] `pytest.ini` (separate)

### ⊕T3 additions
- [ ] `docs/compliance/` per applicable regulations
- [ ] Multi-Dockerfile split
- [ ] `docker-compose.prod.yml`
- [ ] `.github/workflows/audit.yml`
- [ ] `schema/db_struct.sql`

### ⊕T4 additions
- [ ] `ROADMAP.md`, `STARTUP_ROADMAP.md`
- [ ] `docs/business/{STAKEHOLDER_UPDATE,demo_video_script,pricing}.md`
- [ ] `Procfile`
- [ ] `deliverables/` subfolders

If any check fails, setup is incomplete. Fix before declaring ready.

---

## 12. Invocation

```text
[Paste OS_SETUP.md into Claude Code or Kimi]

Project brief:
"""
<paste project PDF text or scope here>
"""

Project tier: T<N>   (T1 default; bump for production / compliance / startup)

Use OS-Setup v1.3 to generate the complete project structure.
Apply tier-T<N> additions per §1.5.
Honor the Brain/Hands/Session triad (§1.6).
Use the unified skills/commands schema (§4.22): allowed-tools + invocation + subagent.
Generate evals/ as a first-class directory with starter tasks (§4.23–24).
Initialize orchestrator/memory/session/ for durable event logging (§4.25).
Honor blast-radius governance r0–r5 (§4.26).
Honor all lessons in §10 v1.3.
Fill all placeholders with project-specific content.
Create folder structure, write all files; ask me only when you genuinely need a
decision I haven't given you.

When done, print:
1. The folder you created
2. The first wave's task files ready to dispatch
3. The starter eval tasks created
4. The exact command to open in Claude Code or Kimi to start
5. Tier-specific extras created (if T2+)
```

---

## 13. Failure-Mode Guardrails (the anti-hallucination teeth)

> Each line below is a REAL failure observed across real projects. The orchestrator wires the relevant ones into the generated project (pre-commit + CI + review) and obeys all of them itself. The `OS-Setup/` folder ships these as executable validator scripts; here they are the rules to enforce.

| # | Failure | Symptom | Prevention rule (enforce always) |
|---|---|---|---|
| FM-01 | **State drift** | duplicate/contradictory rows in EXECUTION/HANDOFF | status files are REWRITTEN to current truth, never appended; one row per item; active-wave must match across files |
| FM-02 | **Stale process** | old run with wrong params burns CPU | before any long job: `ps`-check for an existing run; params come from config, asserted + printed at startup |
| FM-03 | **Broken references** | a doc/script links a deleted file | before delete/rename, grep for inbound refs and fix in the same change; every committed reference resolves |
| FM-04 | **Context bloat** | agent forgets earlier decisions | progressive disclosure; kernel ≤ ~3K tokens; /clear between tasks; compact to HANDOFF/ADR/events.jsonl |
| FM-05 | **Metric inconsistency** | same number stated two ways | metrics live in ONE generated source (`results/metrics.json`); docs reference/regenerate, never hand-type |
| FM-06 | **Config revert** | a param silently changed back | critical params in one config file, asserted at runtime so a revert fails loud; lock the critical keys |
| FM-07 | **Embarrassing artifacts** | cheat-sheets / AI prompts / secrets committed | publish-gate scan before commit/push; working artifacts in `attic/`/`scratch/` (untracked); rotate any leaked secret |
| FM-08 | **Scope creep** | features nobody asked for | `SCOPE_GUARD.md` lists IN/OUT/LATER; every worker brief lists files it may + must-NOT touch; extras → BACKLOG |
| FM-09 | **False status** | "done"/"passes" without proof; misframing | evidence-required (command + output this session); own your bugs; never round "partly" up to "done" |
| FM-10 | **Flaky tests** | pass alone, fail in suite | fresh state per test; seed all RNG; run suite twice shuffled; quarantine+fix, never "re-run until green" |
| FM-11 | **Silent failures** | swallowed errors / hidden fallbacks | no bare `except: pass`; fallbacks log loud; missing required input fails loud, never substitutes synthetic data |
| FM-12 | **Stale derived docs** | README shows old numbers | derived content is GENERATED, never hand-typed; regenerate on /ship; stamp "as of <sha>" |
| FM-13 | **Parallel collisions** | two workers edit one file | wave briefs have DISJOINT write sets (check before dispatch); shared files owned by one early task; else sequence |
| FM-14 | **Lost handoff** | cold new session re-derives wrongly | HANDOFF.md always current; new session reads HANDOFF→kernel→active spec→recent events before acting |

**The failure→prevention loop:** every new CRITICAL bug → add it to this table + a regression test + the guardrail that stops it. The library only grows.

---

## 14. Archetype Engine (auto-tailor the start)

> Detect the project KIND from the brief, then adapt: default tier, what to emphasize, what to skip, and which failure modes to guard first. Load exactly one.

| Archetype | Signals | Tier | Emphasize | Skip | Top FMs |
|---|---|---|---|---|---|
| **hackathon** | "48h", "demo day", judges, speed | T0–T1 | one end-to-end demo path; seeded/offline fallback; the pitch | auth, compliance, exhaustive tests, SDKs | FM-09, FM-02, FM-11 |
| **internship** | mentor/professor, report, presentation | T1–T2 | working deliverable + report + slides; reproducibility; honest limitations | multi-tenancy, billing, heavy compliance | FM-07, FM-09, FM-05, FM-12 |
| **job-take-home** | assessment, "evaluate my code", reviewer | T1 | reviewer UX (README/DECISIONS); clean idiomatic code; right tests; runs first try | over-engineering, infra they didn't ask | FM-07, FM-08, FM-09, FM-10 |
| **research-ml** | paper, experiments, ablations, seeds | T2 | reproducibility; one-source metrics; config-as-law; honest negative results | UI, multi-tenancy, deployment | FM-02, FM-05, FM-06, FM-09, FM-11 |
| **nlp-pipeline** | NER, OCR, extraction, documents | T1–T2 | ingestion robustness; schema-first; golden set; hybrid (rules+LLM) | multi-tenancy, heavy UI | FM-11, FM-05, FM-10, FM-02 |
| **internal-tool** | ERP, admin, "for our team", CRUD | T1–T2 | domain model + lifecycle; RBAC; audit log; vertical slices | multi-tenancy, portals, mobile, AI features | FM-01, FM-13, FM-06, FM-04 |
| **saas-product** | customers, multi-tenant, billing, uptime | T3 | tenant isolation; auth; observability; compliance; reliability | speculative features | FM-07, FM-11, FM-02, FM-01 |
| **startup-mvp** | PMF, first customers, founder, validate | T2+T4 docs | speed to usable; funnel analytics; reversible decisions; business docs | full compliance, multi-region, premature scale | FM-08, FM-09, FM-04, FM-07 |
| **cli-tool** | library, package, npm/pip, SDK | T1 | API design first; docs+examples; semver+changelog; matrix CI; min deps | UI, multi-tenancy, observability | FM-03, FM-05, FM-12, FM-10 |
| **data-pipeline** | ETL, warehouse, analytics, dashboard | T2 | idempotency; data contracts+quarantine; lineage; one transformation layer | UI beyond dashboard, RBAC beyond warehouse | FM-11, FM-02, FM-05, FM-06 |

**Selection:** match signals; on a tie ask ONE multiple-choice question; default `internal-tool` at T1. Mixed projects pick a PRIMARY for structure, pull emphases from a secondary. State which and why.

---

## 15. The Adaptor Engine (the transform)

> What makes this an *adaptoid*, not a static template: it analyzes the brief, pulls only what fits, and emits an executable, tailored setup. Architecture: **independent core + opt-in compatibility adapters** (LangGraph/CrewAI/AutoGen/ADK at the edges only — never a dependency). Output is **executable-first** (configs/specs), human guidance second. Persistence is **runtime-context-checks** before each phase (git hooks/daemons optional, never required — sovereign/air-gapped safe).

### The 6-step transform
```
INGEST   read this file + the brief (+ any existing code/config).
ANALYZE  detect archetype (§14) + tier (§1.5) + domain + constraints + deadline + audience
         + success criteria; identify highest-risk failure modes (§13).
         Ambiguous? ask ≤4 multiple-choice questions; never guess silently.
PULL     the SMALLEST stack that ships the archetype; the skills tasks need;
         the workflow templates that fit; the failure-mode guardrails to wire.
COMPOSE  emit executable artifacts (below) adapted to archetype + tier + stack.
RECORD   write docs/decisions/0002-stack-selection.md (ADR): chosen + why + rejected.
VERIFY   run the guardrail checks (§13); must pass before declaring ready.
```

### Executable-first output (emit these, in this order)
1. **Project structure** (archetype+tier adapted — §2).
2. **Workflow spec** `workflows/<project>.plan.yaml` — waves, tasks (with disjoint `writes` + `forbid`), gates, parallelism, `self_heal` rules, blast-radius tags, executable acceptance.
3. **Tool/skill manifest** — `mcp.json` + `skills.manifest.json` (pinned).
4. **Routing rules** — which model/agent per work type (cost-aware cascade; cheap models for read-heavy/bulk).
5. **Guardrail wiring** — the §13 rules bound to pre-commit + CI + review.
6. **Kernel + briefs** — short `CLAUDE.md`/`KIMI.md` + `work/wave-1/*.md` self-contained task files.
7. **The ADR** (human layer) — the "why" behind the stack.

### Self-heal rules (every wave declares these)
`on_acceptance_fail → revise_brief` · `on_flaky → quarantine_and_fix` (FM-10) · `on_stale_process → kill_and_restart` (FM-02) · `on_drift → regenerate_from_source` (FM-01/05/12) · `on_context_full → handoff_and_clear` (FM-04).

### The invariant
Whatever it adapts, it never violates the kernel methodology and always wires the failure-mode guardrails. Adaptation changes the *what*, never the *discipline*. That — smallest winning stack + the specific guardrails your risk profile needs + an executable plan — is the edge.

---

## End of OS-Setup v2.0-standalone

Single source of truth for the dual-tier agentic project setup. Update this file (not the generated project) when the methodology evolves. The `OS-Setup/` folder is the expandable multi-file edition (executable validators, full failure-mode + archetype + ecosystem libraries); this file embeds their rules inline for one-paste use.

**Changelog**
- **v2.0-standalone (Jun 2026)** — folded the folder's three core systems into the single file: §13 Failure-Mode Guardrails (14 FMs from real scars) · §14 Archetype Engine (10 archetypes → tier/emphasis/skip/top-FMs) · §15 Adaptor Engine (6-step transform + executable-first output + self-heal). Now matches the folder's power for fast standalone starts.
- **v1.3 (May 2026)** — Brain/Hands/Session triad (Anthropic Apr 2026) · durable events.jsonl session log · wake() resume · skills/commands unification with `allowed-tools` + `invocation` + `subagent` frontmatter · evals/ first-class directory · eval-driven development (pass@k, pass^k) · eval anti-patterns · Swiss Cheese verification · transcript review cadence · auto mode for r0/r1 (Anthropic Mar 2026) · blast-radius governance r0–r5 · Harbor/Braintrust/Phoenix framework support · bundled-skills awareness · replay_session.sh.
- **v1.2 (May 2026)** — Tiers · HALL_OF_SHAME · BACKLOG · wave gotchas · operational docs · audit cycle · compliance · multi-Dockerfile · env docker-compose · Procfile · prometheus · skills-lock · workflows/ + state · validators · architecture.png · STAKEHOLDER · STARTUP_ROADMAP · interview runbook · repo meta-doc · ROADMAP separation · EXECUTION commit hashes · failure→prevention loop.
- **v1.1 (May 2026)** — wave terminology · root CLAUDE/HANDOFF/HIERARCHY · attic/ · deliverables/ · expanded tests/ · plural data/ · models/ versioning · prompts/wave-N/.
- **v1.0 (May 2026)** — initial.
