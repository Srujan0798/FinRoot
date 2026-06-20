# Judge Quickstart — FinRoot in 30 seconds

**Zero keys. Zero network. Fully offline.**

FinRoot ships in **Mock mode by default** — deterministic LLM responses, no API keys, no cloud calls. Every answer still runs through the full 6-agent pipeline with self-critique, prudence verification, and audit trail.

---

## 1. Docker (recommended)

```bash
git clone https://github.com/Srujan0798/FinRoot.git && cd FinRoot
docker compose up --build
```

Open **http://localhost:8501** — the dark UI is ready.

## 2. CLI (no Docker)

```bash
pip install -e .[ui]
PYTHONPATH=src python -m interface.cli --mock \
  "Should I rebalance my 70/30 equity portfolio before FY-end?"
```

## 3. Streamlit directly

```bash
PYTHONPATH=src streamlit run src/interface/ui/app.py
```

---

## Showcase queries to try

| # | Query | What to look for |
|---|---|---|
| 1 | **"Should I rebalance my 70/30 equity-debt portfolio before FY-end?"** | Reasoning trace with tool calls, allocation analysis, tax-aware rebalancing suggestion, citations. |
| 2 | **"I earned ₹15 lakh this year. How can I save tax under Section 80C?"** | Deterministic tax engine output, step-by-step 80C breakdown with actual limits, confidence label. |
| 3 | **"I have ₹2 lakh emergency fund. Should I put it all in a small-cap stock?"** | **Prudence refusal.** Agent flags the risk, explains why emergency funds must stay liquid and safe, offers alternatives. This is the trap demo. |

---

## Where the proof lives

| Evidence | Location |
|---|---|
| FRB benchmark numbers | `results/metrics.json` |
| Eval harness reports | `evals/reports/` |
| Demo screenshots + transcripts | `docs/demo/` |
| Architecture diagram | `docs/architecture/architecture.png` |
| Hash-chained audit trail | `src/finroot/audit/` |

---

**One command. No keys. Full pipeline.** That is sovereign financial reasoning.
