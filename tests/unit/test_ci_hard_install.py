"""CI install steps must hard-fail (no ``|| true`` theater on pip install).

Phase-8 / FM-09: a green CI badge is meaningless if dependency install can
silently fail and subsequent steps skip or misreport. Soft-fail is reserved
for informational dependency *advisory* scans (pip-audit), not install.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"

# Workflows that run pytest / evals and must install deps hard.
CRITICAL = ("ci.yml", "test.yml", "evals.yml", "perf_regression.yml")


def test_critical_workflows_exist() -> None:
    for name in CRITICAL:
        path = WORKFLOWS / name
        assert path.is_file(), f"missing workflow {path}"


def test_no_soft_fail_pip_install_on_critical_workflows() -> None:
    """``pip install ... || true`` must not appear in critical install steps."""
    offenders: list[str] = []
    for name in CRITICAL:
        text = (WORKFLOWS / name).read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if "pip install" in stripped and "|| true" in stripped:
                offenders.append(f"{name}:{i}: {stripped}")
    assert not offenders, "Critical CI workflows soft-fail pip install (theater):\n" + "\n".join(
        offenders
    )


def test_security_secrets_and_money_hard_fail() -> None:
    """Security workflow must hard-fail secrets + money-movement guards."""
    text = (WORKFLOWS / "security.yml").read_text(encoding="utf-8")
    assert "block-secrets" in text
    assert "place_order|execute_trade|transfer_funds" in text or "money-movement" in text
    # pip-audit may be non-blocking (advisories), but secrets step must not soft-fail
    for i, line in enumerate(text.splitlines(), 1):
        if "block-secrets" in line:
            assert "|| true" not in line, f"secrets scan soft-fail at line {i}"
