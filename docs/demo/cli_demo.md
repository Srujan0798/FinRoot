# FinRoot CLI Demo

This page showcases FinRoot's reasoning-first CLI running three representative queries in **mock/offline mode** (no external LLM calls).

> **Recording method**: Plain text transcript (asciinema not installed).  
> Run `pip install asciinema` to generate animated `.cast`/`.svg`/`.gif` recordings.

---

## Query 1 — Portfolio Review & Risk Flagging

```bash
python -m interface.cli --mock "Review my portfolio and flag risks"
```

**What to notice:**
- The agent invokes a multi-step reasoning trace: `intent_classifier` → `context_assembler` → `market_data` (4 holdings) → `portfolio_optimizer` → `risk_assessor` → `monte_carlo` (1000 paths).
- Monte Carlo simulation reports **expected return 20.37%** with **16.5% probability of loss**.
- The **SelfCritic fails** (overall=0.54, threshold=0.6) — correctness axis low — demonstrating the agent's self-skepticism even on valid outputs.

[View full transcript → cli_demo.txt (lines 5–100)](../demo/cli_demo.txt)

---

## Query 2 — LTCG Tax Calculation (Equity)

```bash
python -m interface.cli --mock "Calculate tax on ₹2,00,000 LTCG from equity"
```

**What to notice:**
- The `tax_planner` node applies rule **LTCG_EQUITY** (Budget 2024): 10% on gains over ₹1,00,000.
- Computation is **cited**: taxable gain ₹1,00,000 → base tax ₹10,000 + cess ₹400 = **₹10,400** (effective rate 5.2%).
- **SelfCritic passes** (overall=0.68) — the tax rule is deterministic and fully evidenced.

[View full transcript → cli_demo.txt (lines 102–149)](../demo/cli_demo.txt)

---

## Query 3 — Prudence Refusal (Emergency Fund into Speculative Stock)

```bash
python -m interface.cli --mock "Should I put my entire emergency fund into a hot small-cap stock?"
```

**What to notice:**
- The `risk_assessor` detects the **emergency-fund violation** and triggers a prudence check failure.
- Agent **refuses to recommend** the action: *"Recommendation: do not act yet — verify against your full financial picture."*
- Confidence drops to **low**; SelfCritic fails (overall=0.48) — the agent knows its own refusal is correct but flags explainability gaps.

[View full transcript → cli_demo.txt (lines 151–201)](../demo/cli_demo.txt)

---

## Running the Demo Yourself

```bash
# From repo root
export PYTHONPATH=src
export FINROOT_LLM_PROVIDER=mock

# Query 1
python -m interface.cli --mock "Review my portfolio and flag risks"

# Query 2
python -m interface.cli --mock "Calculate tax on ₹2,00,000 LTCG from equity"

# Query 3
python -m interface.cli --mock "Should I put my entire emergency fund into a hot small-cap stock?"
```

## Generating an Animated Cast (Optional)

```bash
pip install asciinema agg  # or: pip install asciinema svg-term
bash scripts/record_cli_demo.sh
# Outputs: docs/demo/cli_demo.cast, .svg, .gif
```