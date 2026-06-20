"""Root conftest.py — shared fixtures and process lifecycle."""

import atexit
import os
import sys

# Force mock mode for all tests to avoid live API calls
os.environ.setdefault("FINROOT_LLM_PROVIDER", "mock")


def _force_exit():
    """Force-exit after tests to prevent hanging from non-daemon threads."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


# Register forced exit only when running under pytest (not normal Python)
if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
    atexit.register(_force_exit)
