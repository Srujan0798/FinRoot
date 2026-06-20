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

## Research
- [x] **FinBERT vs LLM-judge agreement study** · grader calibration · M · earliest wave-9
- [ ] **Local model quality ladder (8B → 70B) impact on FRB** · sovereignty/quality trade-off · M · earliest wave-10
