# Wave 7 — Interface & Demo

**Goal:** the finance-grade demo surface that makes reasoning *visible* to judges — Streamlit dark
UI (chat + live reasoning trace + Digital Twin viewer + harness tab), Typer CLI, and Mock mode for
zero-friction judging. **UI shell can start after W1; full UI after W4/W5.**

## Tasks (5)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Typer CLI (chat + --mock) | frontend/backend | `src/interface/cli/**` | W4 |
| 02 | Streamlit app shell + dark theme | frontend | `src/interface/ui/app.py`, `src/interface/ui/theme.py` | W1 |
| 03 | Chat + reasoning-trace panel | frontend | `src/interface/ui/components/chat.py`, `components/trace.py` | W4,W5 |
| 04 | Digital Twin + portfolio viewer | frontend | `src/interface/ui/components/twin.py` | W2 |
| 05 | Live harness tab (run FRB in-app) | frontend | `src/interface/ui/components/harness.py` | W6 |

## Contracts to freeze first
`ui.contract.md` — the core API the UI/CLI call (one `answer(query, twin) -> Recommendation`
entry point), the trace event shape the UI renders, and the Mock-mode default.

## Acceptance
```bash
python -m src.interface.cli --mock "summarize today's market impact on my portfolio"
streamlit run src/interface/ui/app.py   # loads, Mock mode, no keys; chat + trace + twin + harness tabs
pytest tests/e2e -k ui -v
```
Demo path MUST work fully offline (Mock). Reliability > flashiness at judging.

## Scoring relevance
Solution Idea (15%) + presentation impact across all axes — judges *see* the reasoning trace and the
live harness delta. The UI is how the 35% and 30% become visible.
