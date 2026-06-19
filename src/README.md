# src/ — Architecture Skeleton (workers implement; orchestrator does NOT)

> This is the **documented skeleton**. The OS-Setup deliberately ships directories + this map, NOT
> stub `.py` files — because the exact source files are assigned to worker agents in the wave task
> `Writes` sets (`work/wave-N/*.md`). Pre-creating them would collide with the disjoint-create
> discipline (FM-13). Each file below is created by the worker who owns the task.

## Layout
```
src/
├── finroot/            # the importable package (the agent)
│   ├── llm/            # provider abstraction (Mock/Ollama/Groq/OpenAI)        ← W1·01
│   ├── schemas/        # Pydantic models + LangGraph AgentState                ← W1·02
│   ├── audit/          # hash-chained tamper-evident trail                     ← W1·03
│   ├── utils/          # config glue + helpers                                 ← W1·04
│   ├── tools/          # base.py ← W1·05; 12 concrete tools ← W3
│   ├── agents/         # base.py ← W1·05; orchestrator + 5 sub-agents ← W4
│   ├── memory/         # 4-tier memory + Digital Twin                          ← W2
│   ├── workflows/      # LangGraph graph + context + synthesize                ← W4
│   ├── reasoning/      # Self-Critic, refine, principles, consistency, explain ← W5
│   ├── evaluation/     # FRB harness, baselines, report                        ← W6
│   └── __init__.py     # public exports                                        ← W1·06
└── interface/
    ├── cli/            # Typer CLI (--mock)                                     ← W7·01
    ├── ui/             # Streamlit dark UI (app.py + components/)               ← W7·02..05
    └── api/            # FastAPI (optional)                                     ← (BACKLOG / optional)
```

## Module → wave map (authoritative: plan/ARCHITECTURE.md §11)
| Package | Wave | Task file |
|---|---|---|
| `llm/` | W1 | `work/wave-1/01-llm-provider-layer.md` |
| `schemas/` | W1 | `work/wave-1/02-pydantic-schemas-state.md` |
| `audit/` | W1 | `work/wave-1/03-audit-trail-backbone.md` |
| `utils/` + `config/` | W1 | `work/wave-1/04-config-settings.md` |
| `tools/base.py`, `agents/base.py` | W1 | `work/wave-1/05-base-tool-agent-interfaces.md` |
| `__init__.py`, bootstrap | W1 | `work/wave-1/06-project-bootstrap-ci.md` |
| `memory/` | W2 | `docs/waves/wave-2-brief.md` |
| `tools/*` (12) | W3 | `docs/waves/wave-3-brief.md` |
| `agents/*`, `workflows/` | W4 | `docs/waves/wave-4-brief.md` |
| `reasoning/` | W5 | `docs/waves/wave-5-brief.md` |
| `evaluation/` | W6 | `docs/waves/wave-6-brief.md` |
| `interface/` | W7 | `docs/waves/wave-7-brief.md` |

## How a worker starts
Read `work/WORKER_PROMPT.md` → your task file → the contract it references → implement into your
`Writes` set → tests → report. You may delete the `.gitkeep` in your package dir when you add files.
