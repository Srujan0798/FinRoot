# HANDOFF — Current State

> Replaced 2026-07-25T16:34Z ULTRA WIN loop (mean stretch + judge dry-run).

## Snapshot
- **Honest blended score:** **~96%** — **not 100% / not freeze**
- **FRB @ `fe0ffb6`:** mean **0.9117** · pass@1 **1.0000** · lift **+168.94%** vs RAG
- **Evidence:** `work/reports/wave-ultra/loop-20260725T1634.md`
- **Plan:** `work/ETERNAL_FINAL_PLAN.md` · **Scoreboard:** `docs/SCOREBOARD.md`

## Trajectory
| Stage | % | pass@1 |
|---|---:|---:|
| Audit | 68 | 0.46 |
| Phase 1 GP | 83 | — |
| Domain FRB | 91 | 0.63 |
| Conf soft + tax HIGH | ~94.5 | 0.87 |
| Tax residual | ~95.5 | 1.00 |
| **Now (mean + dry-run)** | **~96** | **1.00** |

## This loop
1. Judge dry-run was RED — principles tests still expected `"No guarantees"` after rename
2. Fixed `tests/unit/test_principles.py` → `"No fixed-return claims"`
3. Soft domain routing: international/behavioral win over TAX/NEWS/RISK/PORTFOLIO when keywords match
4. Expanded intl/behavioral keywords + prose for must_mention coverage
5. Regenerated metrics + zip; `bash scripts/judge_dry_run.sh` → **JUDGE DRY-RUN OK**

## Prove green
```bash
make smoke
bash scripts/judge_dry_run.sh
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1
# expect pass@1=1.0000 mean≈0.9117
```

## Still open for Phase 9 freeze
1. **Commit** dirty tree — then re-`make evals` + ship-prep if SHA ≠ fe0ffb6  
2. True cold-clone stranger path (clean tree / clone, not only local dry-run)  
3. Docker compose smoke (optional)  
4. Human freeze bet  

**Do not claim submission 100% without Phase 9.**
