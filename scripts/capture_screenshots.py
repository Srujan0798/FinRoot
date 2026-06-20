"""Capture PNG screenshots of the FinRoot Streamlit UI for the submission deck.

Launches the Streamlit app in Mock mode, drives it through the 4 demo tabs,
and captures PNG screenshots of each tab for the submission deck / README /
video thumbnails.  Requires Playwright + Chromium.

Usage::

    PYTHONPATH=src python3 scripts/capture_screenshots.py
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_OUTPUT_DIR = _ROOT / "docs" / "demo" / "screenshots"

# (filename, tab_label_substring, query_or_None)
SCREENSHOTS: list[tuple[str, str, str | None]] = [
    ("01_chat_portfolio.png", "Chat", "Review my portfolio and flag risks"),
    ("02_reasoning_trace.png", "Reasoning Trace", None),
    (
        "03_trap_refusal.png",
        "Chat",
        "Should I put my entire emergency fund into a hot small-cap stock?",
    ),
    ("04_digital_twin.png", "Digital Twin", None),
    ("05_harness.png", "Harness", None),
]


def _check_health(port: int, *, retries: int = 30, delay: float = 0.5) -> bool:
    """Poll Streamlit's health endpoint until it responds ok."""
    url = f"http://127.0.0.1:{port}/_stcore/health"
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(delay)
    return False


def main() -> None:
    """Launch Streamlit, drive Playwright, capture screenshots."""
    # --- Lazy-import playwright (fail loud if missing) ---
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        print(
            "FATAL: playwright is not installed.\n"
            "  Install it with:\n"
            "    pip install playwright && playwright install chromium\n",
            file=sys.stderr,
        )
        sys.exit(1)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Find a free port ---------------------------------------------------
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    # --- Launch Streamlit ---------------------------------------------------
    env = {**os.environ, "FINROOT_LLM_PROVIDER": "mock"}
    streamlit_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(_ROOT / "src/interface/ui/app.py"),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
            # Bind to loopback only — this is a transient capture server; the
            # Playwright client connects via 127.0.0.1, so there is no reason to
            # expose it on the LAN (security review: avoid 0.0.0.0 bind).
            "--server.address",
            "127.0.0.1",
            "--browser.gatherUsageStats",
            "false",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        if not _check_health(port):
            msg = (
                streamlit_proc.stderr.read(1024).decode()
                if streamlit_proc.stderr
                else ""
            )
            print(f"FATAL: Streamlit did not start on port {port}\n{msg}", file=sys.stderr)
            sys.exit(1)

        base_url = f"http://127.0.0.1:{port}"

        # --- Drive Playwright -----------------------------------------------
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(base_url, wait_until="networkidle")

            written: list[Path] = []

            for filename, tab_label, query in SCREENSHOTS:
                out_path = _OUTPUT_DIR / filename

                # Click the target tab (filter by text content)
                page.get_by_role("tab").filter(has_text=tab_label).first.click()
                page.wait_for_timeout(500)

                if query is not None:
                    chat_input = page.locator('[data-testid="stChatInput"] textarea')
                    chat_input.fill(query)
                    chat_input.press("Enter")
                    page.wait_for_timeout(5000)

                page.screenshot(path=str(out_path), full_page=True)
                written.append(out_path)

            browser.close()

        print(f"\nDone. {len(written)} screenshot(s) written:")
        for p in written:
            size = p.stat().st_size
            print(f"  {p.relative_to(_ROOT)}  ({size:,} bytes)")

    finally:
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()


if __name__ == "__main__":
    main()
