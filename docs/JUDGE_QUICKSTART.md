# Judge Quickstart — FinRoot in 30 seconds

**Zero keys. Zero network. Fully offline.**

FinRoot ships in **Mock mode by default** — deterministic LLM responses, no API keys, no cloud calls. Every answer still runs through the full multi-agent pipeline with self-critique, prudence verification, and a hash-chained audit trail.

**Headline metric (regenerated, not hand-typed):** see `results/metrics.json`  
(as of last eval: FinRoot mean ~0.866 · pass@1 ~0.506 · composite lift ~+155% vs RAG).

---

## 1. Docker (recommended)

```bash
git clone https://github.com/Srujan0798/FinRoot.git && cd FinRoot
docker compose up --build
```

Open **http://localhost:8501** — dark UI, **Mock Mode** badge, **Not financial advice** banner.

## 2. CLI (no Docker)

```bash
pip install -e ".[ui,dev]"   # dev extra needed for `make judge-dry-run` below
PYTHONPATH=src python -m interface.cli --mock \
  "Should I rebalance my 70/30 equity portfolio before FY-end?"
```

## 3. Streamlit directly

```bash
PYTHONPATH=src streamlit run src/interface/ui/app.py
```

---

## Showcase queries (sacred golden paths)

| # | Query | What a hostile judge should see |
|---|---|---|
| **GP-1** | "Should I rebalance my 70/30 equity portfolio before FY-end?" | PORTFOLIO intent · allocation / concentration · tax-aware rebalance · citations · critic |
| **GP-2** | "What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?" | **TAX domain** (not news blurb) · computed tax (₹0 after ₹1L exemption) · FY 2024-25 rules |
| **GP-3** | "I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?" | **Prudence refuse** · LOW confidence · **do not act yet** · emergency fund first |
| **GP-4** | "Should I take a personal loan to buy more stocks for higher returns?" | **RISK** (not news) · refuse leverage / borrow-to-invest |
| **GP-5** | "Calculate VaR and max drawdown for my portfolio" | **RISK** metrics language · no false "95% single-asset" fail |

> **Note:** the API's first request after boot is ~3x slower than steady-state (~1s vs
> ~0.3s) — a one-time warm-up, not a performance problem. Subsequent requests are fast
> and consistent.

---

## 60-second proof commands

```bash
make smoke
# → FOUNDATION OK

# Full hostile dry-run (smoke + GP locks + live probes + API + metrics)
make judge-dry-run
# → JUDGE DRY-RUN OK

PYTHONPATH=src python -m interface.cli --mock \
  "What is LTCG tax on ₹1,00,000 equity gains held 2 years in India?"
# → "Computed tax…" not "Market news impact"

PYTHONPATH=src python -m pytest tests/golden/test_golden_paths_ps1.py -q
# → sacred GP locks green
```

---

## Where the proof lives

| Evidence | Location |
|---|---|
| FRB numbers | `results/metrics.json` |
| Scoreboard (honest %) | `docs/SCOREBOARD.md` |
| Architecture | `docs/architecture/architecture.png` |
| Screenshots | `docs/demo/screenshots/` |
| Audit trail code | `src/finroot/audit/` |
| Brutal audit | `work/reports/BRUTAL_AUDIT.md` |

---

**One command. No keys. Full pipeline.** Sovereign financial reasoning — with refusal when the request is unsafe.
