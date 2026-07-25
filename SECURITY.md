# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in FinRoot, please report it
privately to the maintainers. **Do not file a public GitHub issue for
security bugs.**

Contact: open a private security advisory on GitHub
(Repository → Security → Advisories → New draft security advisory).

We will acknowledge your report within 72 hours and aim to provide a fix
or mitigation within 30 days for critical issues.

## Supported versions

| Version | Supported          |
|---------|--------------------|
| main    | ✅ Active          |
| < main  | ❌ End-of-life (use main) |

FinRoot is a research / hackathon project. We do not maintain multiple
release branches; only the latest commit on `main` is supported.

## Security model

FinRoot is a **sovereign, locally-runnable** financial reasoning agent.
The default mode is `mock` (no network, no API keys). When the user
opts in to live providers (Ollama / Groq / OpenAI), the data leaves
the local machine — see the provider's own security model.

FinRoot does not:
- Send data to any remote endpoint by default
- Store credentials in the repository (the `.env.example` file is
  gitignored; only the example file is tracked)
- Run with elevated privileges
- Make outbound HTTP calls except those the user explicitly enables
  via `--provider`

The submission zip (`finroot-submission.zip`) is secret-scanned by
`tests/unit/test_zip_consistency.py::test_zip_clean_of_real_key_shapes`
on every CI run.

## Threat model

The intended threat model is:
- Single-user developer workstation
- Local mock LLM (offline)
- No concurrent users
- No multi-tenant data

FinRoot is **not** designed for:
- Multi-user production deployment (no auth, no rate limits)
- Storing real customer PII (the `data/samples/` profiles are
  synthetic)
- Operating in regulated environments without additional review

## Dependencies

We pin transitive dependencies in `requirements.txt` and use
`pip-audit` recommendations in the `scripts/dep_audit.sh` (added in
wave-15/iter27). Security-critical CVEs in the dep tree will be patched
in a follow-up commit and re-stamped via `make evals`.

## Acknowledgments

We thank the security research community for responsible disclosure.
