# Troubleshooting

Common issues and their fixes, in order of likelihood.

## 1. `pytest: command not found`
You need to install dev dependencies. Run `make install` (or
`pip install -e ".[dev]"` directly).

## 2. `ModuleNotFoundError: No module named 'finroot'`
Set `PYTHONPATH=src` for one-off Python commands. Pytest auto-handles this
via `pyproject.toml` (`[tool.pytest.ini_options].pythonpath = ["src"]`).

## 3. The test suite passes locally but fails in CI
- Check `FINROOT_LLM_PROVIDER` — must be `mock` (default) in tests.
- Check `FINROOT_METRICS_PATH` — must NOT be set in CI; the conftest's
  subprocess wrapper sets it per-test to a tmp path.
- The Streamlit/Playwright import may fail in headless CI; the tests skip
  in that case (see `tests/integration/test_cli_smoke.py`).

## 4. The submission zip is missing files
`finroot-submission.zip` is created by `bash scripts/make_submission.sh`
(also `make ship-prep` does this end-to-end). If the zip is missing,
run that command and verify `results/metrics.json` exists.

## 5. `make validate` reports "DRIFT: <file> does not cite HEAD <sha>"
You made a commit but didn't update the docs. Either:
- Run `make evals` then `make ship-prep` (regenerates the metric and
  refreshes the zip).
- Manually update the docs to cite the new HEAD sha.
- Bypass with `git commit --no-verify` only in an emergency.

## 6. `ruff` complains about a line that's fine
`ruff`'s default rule set is "E, F, I, UP, B, SIM, C4, R, S, ASYNC" (see
`pyproject.toml`). The S (security) and R (refactor) sets are noisy in
test code; per-file-ignores handle that. If a real issue is flagged
that you think is a false positive, add a `# noqa: <rule>` comment with
a short justification.

## 7. The harness subprocess test hangs
`tests/unit/test_harness.py::TestSingleTaskMode::test_cli_full_runs`
spawns `scripts/run_evals.py` as a subprocess with a 600s timeout.
On a busy system, the parent pytest can starve the subprocess. Run
the suite with `-m 'not slow'` to skip the slow harness tests during
development.

## 8. `pip-audit` reports CVEs
The `make dep-audit` target reports outdated packages and CVEs. Don't
auto-upgrade — most version bumps will break FinRoot. Instead, check
the specific CVE against `requirements.txt` and bump only the affected
package after running the test suite.

## 9. The doc-link validator reports broken refs in `orchestrator/`
`orchestrator/scripts/validate_doc_links.sh` deliberately skips
`orchestrator/` because orchestrator-internal docs reference files
relative to the repo root (HANDOFF.md, EXECUTION.md, etc.) but live
in `orchestrator/` subdirs. The 86 broken refs the script finds are
in user-facing docs (transcripts, evals/, plan/) and are pre-existing
issues unrelated to the most recent wave.

## 10. `git push` fails the pre-push hook
The pre-push hook runs `validate_execution.sh` + `validate_docs.sh`.
If either fails, fix the issue and re-push. Bypass with
`git push --no-verify` only in an emergency.

## 11. `make cold-check` is too slow
Use `make test-cold -- --fast` (single run instead of 3) or just
`make test-fast` for development iteration.

## 12. The CI test count dropped
Run `make test-pyramid` to see the breakdown. A drop usually means a
test was deleted or skipped. Check `git log --stat` for recent
deletions and the `pytest.mark.slow` registry in `pyproject.toml`.
