# FinRoot Sample Data

This directory contains synthetic sample data for development, testing, and demonstration purposes. **No real PII or financial data is included** — all names, numbers, and identifiers are synthetic.

## Files

### `twin_profiles.json`
Three synthetic `DigitalTwin` profiles compatible with the `DigitalTwin` Pydantic model (`src/finroot/memory/digital_twin.py`). Each profile represents a distinct investor archetype:

| Profile ID | Name | Age | Risk Tolerance | Horizon | Monthly Income | Profile Summary |
|------------|------|-----|----------------|---------|----------------|-----------------|
| `twin_priya_sharma_001` | Priya Sharma | 32 | Conservative | Medium | ₹1,50,000 | Conservative saver prioritizing capital preservation, building emergency fund, child education corpus, and retirement. Portfolio: FDs, balanced/debt MFs, PPF. |
| `twin_rahul_mehta_002` | Rahul Mehta | 45 | Moderate | Medium | ₹4,50,000 | Business owner with volatile cash flow, ESOP lockup, daughter's education goal in 4 years, early retirement target. Portfolio: concentrated equities, flexi/small-cap MFs, FD, large ESOP position. |
| `twin_ananya_iyer_003` | Ananya Iyer | 27 | Aggressive | Long | ₹2,80,000 | High-income tech professional with high savings rate, long horizon, aggressive growth mandate. Portfolio: ESOP, concentrated equities, small-cap/flexi-cap MFs, international ETF. |

**Schema compliance:** Each object validates against `DigitalTwin` (Pydantic v2, `extra="forbid"`). All datetimes are UTC-aware ISO 8601. Holdings are `list[dict]` compatible with the `holdings` JSON column in `DigitalTwinStore`.

### `README.md`
This file.

## Synthetic Data
See `../synthetic/` for generated conversation fixtures used in integration tests.

## Usage in Tests
```python
from finroot.memory.digital_twin import DigitalTwin
import json

with open("data/samples/twin_profiles.json") as f:
    profiles = json.load(f)

priya = DigitalTwin.model_validate(profiles[0])  # Profile A: Conservative
rahul = DigitalTwin.model_validate(profiles[1])  # Profile B: Moderate (business owner)
ananya = DigitalTwin.model_validate(profiles[2]) # Profile C: Aggressive
```

## Regeneration
These are static fixtures. To regenerate with different parameters, see `scripts/generate_samples.py` (if present) or create a new generation script. Do not commit real user data.