# OS-Setup v2.0-standalone — Universal Agentic Project Kickstart

> Paste this file + project brief into Claude/Kimi → complete dual-tier agentic project structure.
> Built from: Anthropic Skills, Boris Cherny best practices, Karpathy CLAUDE.md, 12-Factor Agents,
> 5 canonical patterns, SuperClaude, BMAD, Spec-Kit, Kiro, MCP, A2A, + 5 real shipping projects.
> Plus Anthropic 2026 posts: Brain/Hands/Session triad, eval-driven development, auto mode, blast radius, harness design.

---

## §0 — How to use

1. Open Claude Code or Kimi. 2. Paste this file. 3. Paste project brief. 4. Say:
*"Use OS-Setup v2.0. Run the Adaptor Engine (§15): detect archetype (§14), pick tier (§1.5),
wire failure-mode guardrails (§13), generate complete project structure."*
Engine detects archetype, picks tier, pulls what fits, wires guardrails, creates `<project>/`.

---

## §1 — Two-Tier Methodology

**TIER 1 — Orchestrator** (Claude/Kimi, interchangeable). Plans, writes task files to `work/`,
reviews reports, merges, updates state. **Never writes implementation code.**
**TIER 2 — Workers** (OpenCode CLI windows). Receive ONE self-contained task file from
`work/<wave>/<task>.md`, implement into `src/`, write report to `work/reports/<wave>/<task>.report.md`.
Stateless, parallel. Handoff is the file boundary. Orchestrator never executes; workers never plan.

### §1.5 — Project Tiers (additive: T4 ⊃ T3 ⊃ T2 ⊃ T1 ⊃ T0)

| Tier | Use when | Adds |
|---|---|---|
| **T0** | Solo experiment, weekend hack | CLAUDE.md + work/ + plan/PRD only (~10 files) |
| **T1** | Internal tool, MVP (default) | Full structure: orchestrator/, .specify/, plan/, docs/ (~90 files) |
| **T2** | Production, observability | docs/operational/, docs/audits/, HALL_OF_SHAME, BACKLOG, perf budgets |
| **T3** | Compliance (DPDP/GDPR/HIPAA) | docs/compliance/, multi-Dockerfile, env-specific compose, audit.yml |
| **T4** | Startup, customer-facing | ROADMAP, STARTUP_ROADMAP, docs/business/, Procfile, deliverables/ |

### §1.6 — Brain/Hands/Session Triad (Anthropic Apr 2026)

| Primitive | Our equivalent |
|---|---|
| **Brain** | Claude/Kimi orchestrator reading `orchestrator/` |
| **Hands** | OpenCode CLI worker windows + MCP servers + Docker sandboxes |
| **Session** | `orchestrator/memory/session/<wave>-<task>.events.jsonl` (append-only) |
| `execute(name, input)` | task brief in `work/<wave>/<task>.md` |
| `emitEvent(id, event)` | append to events.jsonl |
| `wake(sessionId)` | reopen Claude/Kimi → HANDOFF.md + events.jsonl restore context |

Failure modes: Brain crash → reopen + resume. Hand crash → provision new window. Session lost → events.jsonl is safety net.

---

## §2 — File Structure

```
<project>/
├── CLAUDE.md / KIMI.md (alias) / AGENTS.md   # kernel, auto-loaded
├── HANDOFF.md                         # current state for cold sessions
├── HIERARCHY.md                       # repo map + ownership
├── README.md · HOW_TO_RUN.md · CHANGELOG.md · CONTRIBUTING.md
├── BACKLOG.md · HALL_OF_SHAME.md      # ⊕T2
├── OS_SETUP.md                        # this file, kept for regeneration
│
├── orchestrator/                      # Tier-1 apparatus (lazy-loaded)
│   ├── ROLE.md · core/ (≥9) · commands/ (≥10, deprecated) · skills/ (≥12)
│   ├── agents/ (≥4) · hooks/ (≥7) · recipes/ · rules/ · memory/
│   │   ├── MEMORY.md · states/ (per-workflow JSON) · session/ (events.jsonl)
│   └── scripts/ (validate, context-budget, validate_execution, replay_session)
│
├── evals/                             # ⊕T1: eval-driven dev (pass@k / pass^k)
│   ├── tasks/ · graders/ · trials/ · transcripts/ · outcomes/ · reports/
│
├── work/                              # THE BRIDGE — orchestrator writes, workers read
│   ├── TASK_TEMPLATE.md · REPORT_TEMPLATE.md · WORKER_PROMPT.md
│   └── wave-N/ · reports/wave-N/
│
├── .specify/                          # Spec-driven (constitution, steering, per-wave specs)
├── plan/                              # PRD · ARCHITECTURE · EXECUTION (3 living docs)
├── docs/                              # waves/ · decisions/ · operational/ ⊕T2 · audits/ ⊕T2
│                                      # compliance/ ⊕T3 · business/ ⊕T4 · architecture/
├── prompts/                           # current/ · archive/ · hybrid/ · wave-N/
├── attic/                             # superseded — NEVER deleted
├── workflows/                         # ⊕T2: declarative JSON workflows + state
│
├── src/ · tests/ · data/ · config/ · scripts/ · models/ · schema/
├── mcp.json · Makefile · Dockerfile · docker-compose.yml · pyproject.toml
├── .pre-commit-config.yaml · .env.example · .gitignore · .dockerignore
└── .github/workflows/                 # ci · test · security · evals · perf ⊕T2 · docs_sync ⊕T2
```

---

## §3 — Adaptation Mechanism

### Variable extraction

| Variable | Source | Example |
|---|---|---|
| `PROJECT_NAME` | Brief title | `rfq-to-boq` |
| `PROJECT_GOAL` | One-line | "Convert RFQ PDFs to structured BOQ" |
| `DOMAIN` | Inferred | NLP / web / ML / ERP |
| `TECH_STACK` | Inferred+asked | Python+FastAPI+React |
| `TIER` | Asked (default T1) | T0–T4 |
| `WAVES` | Decomposition | 4–8 waves with dependency graph |
| `ENTITIES` | Domain model | Material / Quantity / Standard |
| `SUCCESS_METRICS` | Acceptance | F1 ≥ 0.85, <60s |
| `RISKS` | Risk register | OCR noise, scope omission |
| `MCP_SERVERS` | Domain | playwright / serena / tavily |
| `COMPLIANCE` | Regulatory | DPDP / GDPR / HIPAA / none |

### Generation order
1. Folder structure for chosen tier → 2. `plan/{PRD,ARCHITECTURE,EXECUTION}.md` → 3. `.specify/memory/constitution.md` → 4. Per-wave specs → 5. Root files (CLAUDE, HANDOFF, HIERARCHY, README, etc.) → 6. Tier additions → 7. Orchestrator apparatus → 8. Wave-1 task files → 9. Config/CI → 10. Print "Setup complete."

### Ongoing operations
- New wave → `/plan wave-N` → `/dispatch` → workers → `/review` → `/merge` → `/ship`
- Decision → ADR in `docs/decisions/` · Failure → `HALL_OF_SHAME.md` · Gotcha → `docs/waves/wave-N-gotchas.md`
- Old patterns → `attic/`, `docs/historical/`, `prompts/archive/` — never deleted

---

## §4 — Key Templates (condensed)

### HALL_OF_SHAME.md (⊕T2) — failure archive
Pattern: title · date · test/component · severity · root cause · impact · fix (file+commit) · prevention.
Workers grep prior fixes. Orchestrator's `self-evolve` scans before dispatch.

### BACKLOG.md (⊕T2) — parked ideas
Items: title · why · rough size · earliest wave. NOT scheduled. Move to wave only when capacity allows.

### wave-N-gotchas.md (⊕T1) — captured DURING wave
Gotcha: hit-by · workaround · permanent-fix-needed. Workers fill as they hit surprises.

### docs/audits/YYYY-MM-DD-final-audit.md (⊕T2)
Scope → Findings (CRITICAL/HIGH/MEDIUM/LOW) → Sign-off. Run after each wave.

### OBSERVABILITY.md (⊕T2)
Logs (structured JSON) · Metrics (Prometheus/Grafana) · Traces (OTel→Jaeger) · Errors (Sentry).
Alert thresholds: P95 > 1s 5min → page · Error > 1% 5min → page.

### PERFORMANCE_SLOS.md (⊕T2)
Endpoint · Target P95 · Acceptable P95 · Minimum P95. CI fails if P95 exceeds Minimum.

### INCIDENT_RESPONSE_PLAYBOOK.md (⊕T2)
SEV-1..4 · On-call rotation · Response: acknowledge→assess→stabilize→communicate→resolve→post-mortem 48h.

### Skills/Commands Unification (Anthropic May 2026)
`.claude/commands/deploy.md` (legacy) = `.claude/skills/deploy/SKILL.md` (preferred). Both create `/deploy`.
Frontmatter: `allowed-tools` · `invocation` (claude|user|both) · `subagent: true` (isolated context).

### evals/tasks/NNN-name.task.yaml (⊕T1)
Input → Agent execution → Outcome verification → Grader (code-based or LLM-judge) → Trials (k=5).
Anti-patterns: don't grade exact tool sequence · don't reject numerical tolerance · don't share state between trials.

### events.jsonl format (⊕T1)
Append-only JSONL: `{"ts", "id", "type": "task.dispatched|worker.started|report.received|review.decision|merge.complete", ...}`.
`replay_session.sh` reads last N events for `wake()` resume.

### blast-radius.md (⊕T2)
r0 read · r1 local repo (auto) · r2 local services (confirm) · r3 remote/push (confirm) · r4 external humans (always confirm) · r5 money/data-loss (block). Auto mode: r0/r1 only.

### EXECUTION.md row format
`| Wave | Name | Status | Tasks | Commit | Notes |` — one row per wave. Status drift validator catches duplicates.

### validate_execution.sh (⊕T1)
Checks: no duplicate waves · active wave matches HANDOFF.md · shipped waves have commit hash. Runs in CI.

---

## §5 — Workflow Loops

### Wave lifecycle
`PRD → /plan → /dispatch → workers → /review → APPROVE:/merge | REVISE:rewrite | REJECT:attic → /ship → next wave`

### Failure-capture (⊕T2)
`Bug → /diagnose → failing test → fix → HALL_OF_SHAME entry → lint rule/golden test if recurring`

### Audit cycle (⊕T2)
After each wave → `/audit` → CRITICAL blocks ship · HIGH next wave · MEDIUM backlog.
Monthly → docs-sync audit · Quarterly → tech-debt + security audit.

### Eval-driven development (⊕T1, Anthropic Jan 2026)
`Write eval tasks → pass@k=0% → /plan → /dispatch → implement → pass@k climbs → ≥50% at k=5 → graduate to regression → every commit → saturate 100% → add harder tasks → read transcripts weekly → calibrate graders quarterly`

### wake() resume
`Reopen Claude/Kimi → auto-loads CLAUDE.md + HANDOFF.md → read events.jsonl → replay_session.sh → resume`

### Auto mode (Anthropic Mar 2026)
`claude --auto` → skip permission prompts for r0/r1 · r2+ still pauses · logged with autoMode=true.

---

## §6 — Quality Gates

### Risk tiering
| Tier | Examples | Gate |
|---|---|---|
| T0 Auto | Read files, run tests | Execute immediately |
| T1 Log+proceed | Write src/, modify tests | Log to MEMORY.md |
| T2 Await approval | Add deps, change CI | Pause, ask human |
| T3 Block | rm -rf, force-push, drop tables | Block unconditionally |

### Acceptance verification
Orchestrator runs acceptance commands before approving (Boris #1 rule).

### CI enforcement
ci.yml (lint+test) · test.yml (matrix) · security.yml (pip-audit+secrets) · perf_regression.yml ⊕T2 · docs_sync.yml ⊕T2 · audit.yml ⊕T3.

### Drift detection (⊕T2)
Files in CLAUDE.md must exist · unused src/ files → attic/ · ADRs > 1yr get check · validate_execution.sh in CI.

### Failure→Prevention loop (⊕T2)
Every CRITICAL bug → HALL_OF_SHAME entry + regression test + eval task + rule/ADR.

### Swiss Cheese verification (⊕T1, Anthropic Jan 2026)
Pydantic → Lint → Unit → Integration → Acceptance → E2E → Eval tasks → Regression → Perf budget → Verifier sub-agent → Human transcript review → Production monitoring. No single layer catches everything.

### Eval anti-patterns (orchestrator REJECTS these)
1. Brittle grading (numerical precision, hardcoded tool sequences) 2. Ambiguous task specs 3. Class imbalance (no refusals tested) 4. Shared state pollution between trials 5. Bypasses (agent edits DB directly) 6. Saturation (100% pass = no signal).

---

## §7 — Multi-Output Deliverables (⊕T4)

`deliverables/` → paper/ · patent/ · report/ · slides/ · demo/. Each gets own wave.

---

## §8 — Customization Checklist

**T1:** PROJECT_NAME/GOAL/DOMAIN/TECH_STACK · MVP/WAVES/ENTITIES/METRICS/RISKS · MCP_SERVERS · wave-1 tasks · skills.manifest.json · interview_runbook.md
**⊕T2:** BACKLOG · HALL_OF_SHAME · operational docs · baseline audit · prometheus · docker-compose.dev · perf+docs_sync workflows · validate_execution.sh · architecture.png
**⊕T3:** compliance docs · multi-Dockerfile · docker-compose.prod · audit.yml · db_struct.sql
**⊕T4:** ROADMAP · STARTUP_ROADMAP · business docs · Procfile · deliverables/

---

## §9 — Open Standards

agentskills.io (skills) · MCP (mcp.json) · A2A (optional) · Spec-Kit SDD (.specify/) · Kiro steering · ADRs (decisions/) · Conventional Commits · Keep a Changelog · SemVer · 12-Factor App+Agents · OpenAPI · OpenTelemetry · Procfile spec

---

## §10 — Version History

| Version | Key additions |
|---|---|
| v1.0 | Initial dual-tier methodology |
| v1.1 | Wave terminology · root CLAUDE/HANDOFF/HIERARCHY · attic/ · expanded tests/ |
| v1.2 | Tiers T0–T4 · HALL_OF_SHAME · BACKLOG · gotchas · operational docs · audits · compliance · multi-Dockerfile · env compose · Procfile · prometheus · skills-lock · workflows/ · validators · architecture.png · stakeholder docs · interview runbook · EXECUTION commit hashes |
| v1.3 | Brain/Hands/Session triad · events.jsonl · wake() resume · skills/commands unification (allowed-tools+invocation+subagent) · evals/ first-class · eval-driven dev (pass@k/pass^k) · anti-patterns · Swiss Cheese · transcript review · auto mode r0/r1 · blast-radius r0–r5 · Harbor/Braintrust/Phoenix · replay_session.sh |
| v2.0 | Folded folder's 3 core systems into single file: §13 Failure-Mode Guardrails (14 FMs) · §14 Archetype Engine (10 archetypes) · §15 Adaptor Engine (6-step transform) |

---

## §11 — Final Self-Check

**T1:** Root files (CLAUDE, KIMI, AGENTS, HANDOFF, HIERARCHY, README, HOW_TO_RUN, CHANGELOG, CONTRIBUTING, Makefile, mcp.json, requirements, pyproject, pre-commit, gitignore, env.example, Dockerfile, compose, skills.manifest) · .claude/settings.local.json · orchestrator/ (ROLE, core≥9, commands≥10, skills≥12, agents≥4, hooks≥6, recipes, rules, memory, scripts≥4) · work/ (templates, wave-1 populated, reports) · evals/ (README, tasks≥5, graders, trials, transcripts, outcomes, reports) · .specify/ (constitution, wave-1 specs) · plan/ (PRD, ARCHITECTURE, EXECUTION filled) · docs/ (decisions, waves, SCOPE_GUARD, runbook, conventions, interview_runbook) · prompts/ (current, archive, INDEX) · attic/ (empty) · tests/ (7 dirs) · src/ skeleton · .github/workflows/ (ci, test, security, evals) · No {{PLACEHOLDER}} remains.
**⊕T2:** +BACKLOG, HALL_OF_SHAME, operational docs, baseline audit, architecture/, schemas/, flows/, benchmarks/, runtime/, REPOSITORY_STRUCTURE, prometheus, docker-compose.dev, architecture.png, perf+docs_sync workflows, validate_execution.sh, workflows/, memory/states/, pytest.ini
**⊕T3:** +compliance docs, multi-Dockerfile, docker-compose.prod, audit.yml, db_struct.sql
**⊕T4:** +ROADMAP, STARTUP_ROADMAP, business docs, Procfile, deliverables/

---

## §12 — Invocation

```
[Paste OS_SETUP.md into Claude Code or Kimi]

Project brief: """<paste brief>"""
Project tier: T<N> (T1 default)

Use OS-Setup v2.0 to generate complete project structure.
Apply tier-T<N> additions per §1.5. Honor Brain/Hands/Session (§1.6).
Use unified skills schema (§4.22): allowed-tools + invocation + subagent.
Generate evals/ as first-class directory (§4.23–24).
Initialize orchestrator/memory/session/ for durable events (§4.25).
Honor blast-radius r0–r5 (§4.26). Fill all placeholders.

When done, print: 1. Folder created 2. Wave-1 task files 3. Starter eval tasks 4. Command to start 5. Tier extras
```

---

## §13 — Failure-Mode Guardrails

| # | Failure | Symptom | Prevention |
|---|---|---|---|
| FM-01 | State drift | duplicate/contradictory rows | status files REWRITTEN to truth, one row per item, active-wave matches across files |
| FM-02 | Stale process | wrong params burns CPU | ps-check before long job; params from config, asserted at startup |
| FM-03 | Broken references | doc links deleted file | grep inbound refs before delete/rename; fix in same change |
| FM-04 | Context bloat | agent forgets decisions | progressive disclosure; kernel ≤3K tokens; /clear between tasks |
| FM-05 | Metric inconsistency | same number two ways | metrics in ONE source (results/metrics.json); docs regenerate, never hand-type |
| FM-06 | Config revert | param silently changed back | critical params in one config, asserted at runtime so revert fails loud |
| FM-07 | Embarrassing artifacts | secrets/prompts committed | publish-gate scan before commit; working artifacts in attic/ untracked |
| FM-08 | Scope creep | features nobody asked for | SCOPE_GUARD.md IN/OUT/LATER; worker briefs list allowed+forbidden files; extras→BACKLOG |
| FM-09 | False status | "done" without proof | evidence-required (command+output this session); own bugs; never round "partly" to "done" |
| FM-10 | Flaky tests | pass alone, fail in suite | fresh state per test; seed RNG; run suite twice shuffled; quarantine+fix |
| FM-11 | Silent failures | swallowed errors | no bare except:pass; fallbacks log loud; missing input fails loud, never synthetic data |
| FM-12 | Stale derived docs | old numbers in README | docs GENERATED, never hand-typed; regenerate on /ship; stamp "as of sha" |
| FM-13 | Parallel collisions | two workers edit one file | DISJOINT write sets per wave; shared files owned by one task; else sequence |
| FM-14 | Lost handoff | cold session re-derives wrongly | HANDOFF.md always current; new session reads HANDOFF→kernel→spec→events |

Every CRITICAL bug → add to this table + regression test + guardrail. Library only grows.

---

## §14 — Archetype Engine

| Archetype | Signals | Tier | Emphasize | Skip | Top FMs |
|---|---|---|---|---|---|
| hackathon | 48h, demo day, judges | T0–T1 | one demo path; seeded/offline; the pitch | auth, compliance, exhaustive tests | FM-09,02,11 |
| internship | mentor, report, presentation | T1–T2 | deliverable+report+slides; reproducibility; honest limits | multi-tenancy, billing | FM-07,09,05,12 |
| job-take-home | assessment, reviewer | T1 | reviewer UX; clean code; right tests; runs first try | over-engineering | FM-07,08,09,10 |
| research-ml | paper, experiments, ablations | T2 | reproducibility; one-source metrics; config-as-law | UI, multi-tenancy, deploy | FM-02,05,06,09,11 |
| nlp-pipeline | NER, OCR, extraction | T1–T2 | ingestion robustness; schema-first; golden set | multi-tenancy, heavy UI | FM-11,05,10,02 |
| internal-tool | ERP, admin, CRUD | T1–T2 | domain model; RBAC; audit log; vertical slices | multi-tenancy, portals, mobile | FM-01,13,06,04 |
| saas-product | customers, multi-tenant, billing | T3 | tenant isolation; auth; observability; compliance | speculative features | FM-07,11,02,01 |
| startup-mvp | PMF, first customers | T2+T4 | speed to usable; funnel analytics; reversible decisions | full compliance, premature scale | FM-08,09,04,07 |
| cli-tool | library, package, SDK | T1 | API design; docs+examples; semver; min deps | UI, multi-tenancy | FM-03,05,12,10 |
| data-pipeline | ETL, warehouse, analytics | T2 | idempotency; data contracts; lineage | UI beyond dashboard | FM-11,02,05,06 |

Match signals; tie → ask ONE multiple-choice question; default `internal-tool` at T1.

---

## §15 — Adaptor Engine

Architecture: independent core + opt-in compatibility adapters (LangGraph/CrewAI/AutoGen/ADK at edges only). Output: executable-first (configs/specs), human guidance second.

### 6-step transform
```
INGEST   read this file + brief (+ existing code/config)
ANALYZE  detect archetype (§14) + tier (§1.5) + domain + constraints + deadline + audience
         + success criteria + highest-risk FMs (§13). Ambiguous? ask ≤4 MCQs.
PULL     smallest stack that ships the archetype; skills; workflow templates; guardrails
COMPOSE  emit executable artifacts adapted to archetype+tier+stack
RECORD   write docs/decisions/0002-stack-selection.md (ADR): chosen+why+rejected
VERIFY   run guardrail checks (§13); must pass before declaring ready
```

### Executable-first output (this order)
1. Project structure (archetype+tier adapted) 2. Workflow spec `workflows/<project>.plan.yaml` (waves, tasks with disjoint writes+forbid, gates, parallelism, self_heal, blast-radius tags, acceptance) 3. Tool/skill manifest (mcp.json + skills.manifest.json pinned) 4. Routing rules (cost-aware cascade) 5. Guardrail wiring (§13 → pre-commit+CI+review) 6. Kernel + wave-1 briefs 7. ADR (the "why")

### Self-heal rules
`on_acceptance_fail → revise_brief` · `on_flaky → quarantine_and_fix` (FM-10) · `on_stale → kill_and_restart` (FM-02) · `on_drift → regenerate_from_source` (FM-01/05/12) · `on_context_full → handoff_and_clear` (FM-04)

### Invariant
Whatever it adapts, it never violates kernel methodology and always wires failure-mode guardrails. Adaptation changes the *what*, never the *discipline*.

---

*End of OS-Setup v2.0-standalone. Update this file when methodology evolves. The `OS-Setup/` folder is the expandable multi-file edition with executable validators.*
