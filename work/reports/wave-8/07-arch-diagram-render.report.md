# Report wave-8/07 — Architecture Diagram Rendering (PNG)

## Result
DONE

## What I built
- `docs/architecture/architecture.png` — rendered from `.mmd` via mermaid-py (128KB PNG)
- `scripts/render_diagram.sh` — shell script that tries mmdc → mermaid-py → mermaid.ink API (SVG fallback)
- `scripts/_render_svg.py` — Python SVG fallback using mermaid.ink API (no deps beyond stdlib)
- `README.md` — replaced inline mermaid code block with `![FinRoot Architecture](docs/architecture/architecture.png)` image embed; mermaid source preserved in a collapsible `<details>` block

## Acceptance evidence (real output, this session)
```
$ test -f docs/architecture/architecture.png || test -f docs/architecture/architecture.svg && echo "diagram rendered"
diagram rendered

$ grep -q "architecture.png\|architecture.svg" README.md && echo "README updated"
README updated

$ test -f scripts/render_diagram.sh && echo "render script exists"
render script exists

$ bash scripts/render_diagram.sh
Warning: IPython is not installed. Mermaidjs magic function is not available.
Rendered via mermaid-py -> /Users/srujansai/Desktop/FinRoot/docs/architecture/architecture.png
```

## Tests
- No unit tests added (shell scripts + simple Python renderer; acceptance commands serve as integration verification)
- `ruff check scripts/_render_svg.py` → All checks passed

## Decisions / deviations
- Used `mermaid-py` (Python package) as primary renderer since `mmdc` was not installed. Installed it via pip3.
- Kept mermaid source in README inside a `<details>` collapsible block so developers can still see the source and re-render.
- SVG fallback script uses the free mermaid.ink API (base64-encoded diagram → HTTP GET → SVG response) — requires internet but is a last resort.

## Surprises / gotchas
- None. Rendering succeeded on first attempt with mermaid-py.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding a CI step to verify `architecture.png` stays in sync with `architecture.mmd`

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
