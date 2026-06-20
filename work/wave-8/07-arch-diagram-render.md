# Task wave-8/07 — Architecture Diagram Rendering (PNG)

> Read `work/WORKER_PROMPT.md` then build. Renders the mermaid diagram to PNG for README.

## Objective
Render `docs/architecture/architecture.mmd` to PNG and embed it in the README, so judges see the architecture without needing a mermaid renderer.

## Writes (ONLY these)
- `docs/architecture/architecture.png` (rendered from .mmd)
- `scripts/render_diagram.sh` (re-render script)
- `README.md` (UPDATE — embed the PNG image)

## Forbid
All other files.

## Steps
1. Read `docs/architecture/architecture.mmd` — understand the mermaid diagram.
2. Create `scripts/render_diagram.sh`:
   - Uses `mmdc` (mermaid CLI) if available, or falls back to a Python mermaid renderer
   - If neither available, use a free online mermaid renderer API (https://mermaid.ink)
   - Outputs to `docs/architecture/architecture.png`
3. Render the diagram to PNG. If mmdc is not installed:
   - `pip install mermaid-py` or use `https://mermaid.ink/img/{base64}` URL approach
   - Or create a high-quality ASCII art version as fallback
4. Update README.md: replace the mermaid code block with an image embed:
   - `![FinRoot Architecture](docs/architecture/architecture.png)`
   - Keep the mermaid source as a comment/link for developers
5. If PNG rendering fails (no internet, no mmdc), create a `docs/architecture/architecture.svg` using Python's built-in SVG generation (no deps needed)

## Acceptance
```bash
test -f docs/architecture/architecture.png || test -f docs/architecture/architecture.svg && echo "diagram rendered"
grep -q "architecture.png\|architecture.svg" README.md && echo "README updated"
test -f scripts/render_diagram.sh && echo "render script exists"
```

## Report
`work/reports/wave-8/07-arch-diagram-render.report.md`
