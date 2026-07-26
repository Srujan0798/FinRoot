# Backlog

> Parked ideas. NOT scheduled. NOT promised. Each: title · why · rough size · earliest wave.
> Move into a wave only when capacity allows and the need is real (FM-08 anti scope-creep).

## Features
- [x] **Multi-currency / FX-aware reasoning** · NRI & cross-border users · M · earliest wave-9
- [ ] **Voice / WhatsApp interface** · field accessibility · M · earliest wave-10
- [ ] **Brokerage API integration (read-only)** · live holdings sync · L · earliest wave-9
- [x] **Goal-based planning wizard** · retirement / education corpus · M · earliest wave-9
- [x] **PDF statement ingestion (CAS/AMC)** · auto-build the Digital Twin · M · earliest wave-9

## Reasoning / quality
- [x] **Adversarial eval set (red-team prompts)** · catch unsafe advice · M · earliest wave-9
- [x] **Counterfactual explanations** · "what would change my recommendation" · M · earliest wave-10
- [ ] **Calibration of confidence labels vs outcomes** · trust · L · earliest wave-10

## Tech debt / infra
- [ ] **Postgres + pgvector instead of SQLite + Chroma** · multi-user scale · L · earliest wave-10
- [ ] **Streaming token output in UI** · perceived latency · S · earliest wave-8
- [x] **Distributed tracing (OpenTelemetry → Jaeger)** · deep observability · M · earliest wave-9
- [ ] **Bump langchain/langgraph past version ceilings (0.3.x/0.2.x → 1.x)** · patches 14
      real PYSEC-backed CVEs (RCE-class in langgraph-checkpoint, SSRF/path-traversal in
      langchain-core) currently blocked by this repo's own `<0.4`/`<0.3` pins · needs a
      dedicated wave with a full regression pass (StateGraph API, checkpoint interfaces,
      message schemas can all change across majors) — do NOT attempt as a quick patch under
      time pressure · L · see docs/SCOREBOARD.md §F for full disclosure and risk assessment
- [ ] **Replace keyword-override domain routing with semantic classification** ·
      `detect_domain()`'s literal-substring override lists (`src/finroot/workflows/
      synthesize.py`) are structurally paraphrase-fragile — HALL_OF_SHAME Patterns 1, 8, 9,
      10, 11 found 8+ confirmed misroutes this session alone, all reactive fixes, not a
      preventive architecture · an embedding-similarity check against domain exemplars (or a
      small classifier) would be durable where literal keyword lists cannot be · M/L ·
      earliest wave-16

## Research
- [x] **FinBERT vs LLM-judge agreement study** · grader calibration · M · earliest wave-9
- [ ] **Local model quality ladder (8B → 70B) impact on FRB** · sovereignty/quality trade-off · M · earliest wave-10
