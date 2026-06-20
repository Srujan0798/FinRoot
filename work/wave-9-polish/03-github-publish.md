# Task wave-9/03 — GitHub Publish Helper + Release Notes (the repo link judges asked for)

> Read `work/WORKER_PROMPT.md` then build. Prepares the repo for a clean public push + a tagged
> release. Depends on all waves (shipped). Blast radius r3 (remote push) — the SCRIPT only pushes
> when the human runs it with a confirm flag; building the script is r1.

## Writes (ONLY these)
- `scripts/publish_github.sh`
- `docs/RELEASE_NOTES.md`

## Forbid
All other files. Do NOT run any `git push` / `gh repo create` yourself — only WRITE the script.
(FM-07 / blast radius: the human runs it after review.)

## Steps
1. `scripts/publish_github.sh` (bash, `set -euo pipefail`):
   - Pre-flight checks (fail loud): clean working tree, tests pass hint, no `.env` tracked, no
     secrets in `git ls-files` (grep for `*.key`, `.env`), `results/metrics.json` present.
   - Requires `gh` CLI authenticated; if missing, print the install/auth hint and exit non-zero.
   - Usage: `publish_github.sh <repo-name> [--private] [--confirm]`.
     - Without `--confirm`: DRY RUN — print exactly what it would do (create repo, push main, tag,
       create release) and exit 0. (Default is dry-run for safety — blast radius r3.)
     - With `--confirm`: `gh repo create <name> --source=. --push` (visibility per flag),
       then `git tag -a v1.0.0 -m "FinRoot v1.0.0 — SCALE PS-1 submission"` and
       `gh release create v1.0.0 --notes-file docs/RELEASE_NOTES.md --title "FinRoot v1.0.0"`,
       and attach `finroot-submission.zip` if present.
   - Print the resulting repo URL on success.
2. `docs/RELEASE_NOTES.md` — v1.0.0 notes: one-paragraph what-it-is, the 4 scoring axes mapped,
   the FRB headline (read the lift from `results/metrics.json`, do NOT hand-type — FM-12: include a
   one-line `python3 -c` snippet the author runs to fill the number, or read it at write time and
   stamp the as_of_sha), quickstart (docker + cli + streamlit), and the demo-asset locations
   (`docs/demo/`, screenshots, cast).

## Acceptance
```bash
bash scripts/publish_github.sh finroot-demo            # DRY RUN — prints plan, exits 0, pushes NOTHING
grep -qi "v1.0.0" docs/RELEASE_NOTES.md && echo "release notes present"
ruff --version >/dev/null 2>&1 || true   # (script is bash; no ruff needed)
bash -n scripts/publish_github.sh && echo "script syntax OK"
```
The dry run MUST NOT create a repo or push. Confirm in the report that the default path is dry-run.

## Report
`work/reports/wave-9-polish/03-github-publish.report.md`
