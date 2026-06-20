# Wave 12 Final — Gotchas

## 02 — Final Speaker-Ready Deck

1. **No `contracts/` dir for wave-12-final.**
   The task brief references `.specify/specs/wave-12-final/contracts/` but the directory does not
   exist in this checkout (sibling tasks `01`, `03`, `04` of the same wave also run without one).
   Looks like a deliberate omission for the docs-only wave. If the orchestrator wants wave shape
   consistency, consider creating the dir (even empty) for traceability.

2. **Numbers drift across docs.**
   The current `results/metrics.json` (as_of_sha `ee438ae`, generated 2026-06-20T15:04) reports
   **83 tasks, 11 domains, +128% composite lift vs RAG, FinRoot mean 0.778**. The deck uses
   these numbers. But `README.md` and `docs/business/presentation_outline.md` still cite the
   older run (52 tasks, +99.7% lift, FinRoot mean 0.672). Follow-up: rerun `make evals` and
   refresh those files in a wave-13 docs-pass — not in scope for this task (FM-08).

3. **Slide 5 trap screenshot choice.**
   `docs/demo/screenshots/03_trap_refusal.png` shows the agent refusing to recommend putting
   an emergency fund into a hot small-cap stock — i.e. the literal "trap refusal" called out
   in the task brief. Use this asset, not `01_chat_portfolio.png` (which is a benign portfolio
   query) or `02_reasoning_trace.png` (which is the trace panel — better as a backup).

4. **Lift percentages on Slide 4.**
   The deck quotes per-domain lifts (portfolio +346%, tax +203%, etc.) computed directly from
   the per-domain `mean_score` blocks in `results/metrics.json` (FinRoot minus RAG, divided by
   RAG). The composite +128% (from `composite_lift_vs_rag_pct`) is a weighted aggregate, not a
   simple mean of the per-domain lifts — they're consistent but not identical.
