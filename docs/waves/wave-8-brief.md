# Wave 8 — Deploy, Docs & Submission Package

**Goal:** make it shippable and judge-ready — Docker one-command spin-up, polished docs/ADRs, the
7-minute demo script, the 6-slide deck, the executive summary, the architecture diagram, and the
submission zip. **Depends on all prior waves.**

## Tasks (6)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | Dockerfile + compose hardening + healthcheck | devops | `Dockerfile`, `docker-compose.yml`, `.dockerignore` | W7 |
| 02 | README polish + judging-criteria mapping | docs | `README.md`, `docs/SUBMISSION.md` | all |
| 03 | ADR set (5–8 decisions) | docs/architecture | `docs/decisions/0003-*.md … 0008-*.md` | all |
| 04 | 7-minute demo script (timed narration) | demo | `docs/business/7_minute_demo_script.md` | W7 |
| 05 | 6-slide deck outline + exec summary | demo | `docs/business/presentation_outline.md`, `docs/business/executive_summary.md` | all |
| 06 | Architecture diagram (mermaid → png) + submission zip | docs/devops | `docs/architecture/architecture.mmd`, `scripts/make_submission.sh` | all |

## Acceptance
```bash
docker compose up -d && curl -fsS localhost:8501 >/dev/null && docker compose down   # UI serves
bash scripts/make_submission.sh         # produces finroot-submission.zip (excludes secrets, caches)
make evals                              # final metrics regenerated → numbers in docs match (FM-12)
```
Derived numbers in README/slides are regenerated from `results/metrics.json`, never hand-typed.

## Scoring relevance
Code Implementation (20%) — deployability + engineering polish; and the demo/docs are how all four
axes are *communicated* to judges. This wave converts the build into the win.

> Note: `docs/business/` is a T4 folder; we pull it in here for the demo/submission deliverables
> only (additive, justified — not a full T4 bump).
