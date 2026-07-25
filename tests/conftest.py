"""Root conftest.py — shared fixtures and process lifecycle."""

import os
import subprocess
import sys
import tempfile

import pytest

import finroot.memory.digital_twin
import finroot.memory.semantic
from finroot.utils import config as _finroot_config

_DEFAULT_TWIN_DB_PATH = "data/digital_twin.db"
_DEFAULT_CHROMA_DIR = "data/chroma"

# Force mock mode for all tests to avoid live API calls.
os.environ.setdefault("FINROOT_LLM_PROVIDER", "mock")

# ---------------------------------------------------------------------------
# Module-level env vars: must be set BEFORE any test module is imported.
# ---------------------------------------------------------------------------
# ``FINROOT_METRICS_PATH`` is read at import time by
# ``src/finroot/evaluation/harness.DEFAULT_METRICS_PATH`` and by
# ``scripts/run_evals.py``'s ``--out`` default.  If we don't set it here,
# the test module's ``from finroot.evaluation.harness import DEFAULT_METRICS_PATH``
# binds the literal ``Path("results/metrics.json")`` at import time, and
# ``str(DEFAULT_METRICS_PATH)`` in the test's ``--out`` arg then forces the
# subprocess to clobber the canonical metrics file.  Setting it here, at
# conftest load (which precedes all test module imports), redirects the
# subprocess's ``--out`` to a session-scoped tmp path so it can't pollute
# ``results/metrics.json``.
_SESSION_TMPDIR = tempfile.mkdtemp(prefix="finroot-conftest-")
os.environ.setdefault("FINROOT_METRICS_PATH", os.path.join(_SESSION_TMPDIR, "metrics.json"))


def _wrap_twin_init(orig_init, redirected_path: str):
    """Wrap ``DigitalTwinStore.__init__`` to redirect the default literal.

    Callers that pass an EXPLICIT, non-default path get that path honored —
    only the default literal sentinel is rewritten.  The class identity is
    preserved (only ``__init__`` is swapped), so ``isinstance`` checks in
    ``MemoryManager`` still succeed.
    """

    def _new_init(self, db_path: str = _DEFAULT_TWIN_DB_PATH) -> None:
        if db_path == _DEFAULT_TWIN_DB_PATH:
            db_path = redirected_path
        orig_init(self, db_path)

    return _new_init


def _wrap_semantic_init(orig_init, redirected_path: str):
    """Wrap ``SemanticMemory.__init__`` to redirect the default literal.

    Same contract as :func:`_wrap_twin_init`.
    """

    def _new_init(
        self,
        persist_dir: str = _DEFAULT_CHROMA_DIR,
        collection: str = "finroot",
    ) -> None:
        if persist_dir == _DEFAULT_CHROMA_DIR:
            persist_dir = redirected_path
        orig_init(self, persist_dir, collection)

    return _new_init


def _build_subprocess_env(base_env: dict[str, str] | None) -> dict[str, str]:
    """Inject hermeticity env vars into a subprocess env.

    The two subprocess tests in ``tests/unit/test_harness.py`` spawn
    ``scripts/run_evals.py`` as a subprocess.  The subprocess has fresh
    Python modules — the in-process ``monkeypatch.setattr`` on the class
    ``__init__`` does NOT propagate.  Without this injection the subprocess
    would resolve ``get_settings().chroma_dir`` and
    ``get_settings().digital_twin_db`` from the *parent's* env, which is
    not set (we deliberately don't set ``FINROOT_CHROMA_DIR`` in the parent
    because ``tests/unit/test_config.py::test_default_paths`` asserts
    ``s.chroma_dir == "data/chroma"`` against a fresh ``Settings()``).

    This wrapper only touches the env passed to ``subprocess.run`` /
    ``subprocess.Popen``; the parent process's env is untouched.
    """
    env = dict(base_env) if base_env is not None else dict(os.environ)
    # Only inject if the caller hasn't already set these (test may want to
    # exercise the default path).
    env.setdefault("FINROOT_CHROMA_DIR", os.path.join(_SESSION_TMPDIR, "chroma"))
    env.setdefault("FINROOT_DIGITAL_TWIN_DB", os.path.join(_SESSION_TMPDIR, "digital_twin.db"))
    # FINROOT_METRICS_PATH is already set at module load; just ensure it's
    # carried into the subprocess env.
    env.setdefault("FINROOT_METRICS_PATH", os.path.join(_SESSION_TMPDIR, "metrics.json"))
    return env


_orig_subprocess_run = subprocess.run
_orig_subprocess_popen = subprocess.Popen


def _wrapped_subprocess_run(*args, **kwargs):
    """Wrapper around ``subprocess.run`` that injects hermeticity env vars.

    We only touch the ``env`` kwarg; if the caller didn't pass one, we use
    ``os.environ`` (so the subprocess inherits the parent's env PLUS our
    injections).  If the caller passed an env, we merge our injections
    into it (caller's values win).
    """
    if "env" in kwargs and kwargs["env"] is not None:
        kwargs["env"] = _build_subprocess_env(kwargs["env"])
    else:
        kwargs["env"] = _build_subprocess_env(None)
    return _orig_subprocess_run(*args, **kwargs)


def _wrapped_subprocess_popen(*args, **kwargs):
    """Same injection for ``subprocess.Popen``."""
    if "env" in kwargs and kwargs["env"] is not None:
        kwargs["env"] = _build_subprocess_env(kwargs["env"])
    else:
        kwargs["env"] = _build_subprocess_env(None)
    return _orig_subprocess_popen(*args, **kwargs)


# Install the wrappers at conftest load time so every test in the run
# gets the injection, regardless of fixture order.
subprocess.run = _wrapped_subprocess_run
subprocess.Popen = _wrapped_subprocess_popen


@pytest.fixture(autouse=True)
def _redirect_persistent_state(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Redirect ChromaDB and DigitalTwin paths to a per-test tmp dir.

    Production code in ``interface.core._build_memory``,
    ``finroot.evaluation.harness._run_finroot``, and
    ``finroot.memory.manager.MemoryManager.create`` now routes through
    ``get_settings().chroma_dir`` and ``get_settings().digital_twin_db``
    (post wave-14/01).  This fixture:

    1. Patches the class ``__init__`` methods in place to redirect the
       default literal — the in-process layer (FM-13: cross-test
       contamination from accumulated on-disk state).
    2. Sets ``FINROOT_DIGITAL_TWIN_DB`` in the parent's env so any
       subprocess spawned during the test inherits it.  We deliberately
       do NOT set ``FINROOT_CHROMA_DIR`` here because
       ``tests/unit/test_config.py::test_default_paths`` asserts the
       default ``s.chroma_dir == "data/chroma"`` against a fresh
       ``Settings()`` (pydantic-settings reads env vars at construction).
       The subprocess layer's chroma redirect is handled by the
       ``subprocess`` wrappers installed at module load above.
    3. Rebinds the imported class names on the three consumer modules
       that hold a pre-resolved reference (same rationale as wave-13/01).
    4. No-ops the ``_ensure_writeable_dir`` / ``_ensure_writeable_parent``
       helpers in ``finroot.utils.config`` so ``assert_settings`` (called
       by ``test_config.py``) doesn't create ``data/chroma`` or
       ``logs/audit.jsonl`` in the repo root.
    """
    chroma_dir = tmp_path / "chroma"
    twin_db = tmp_path / "digital_twin.db"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    twin_init = _wrap_twin_init(
        finroot.memory.digital_twin.DigitalTwinStore.__init__,
        str(twin_db),
    )
    sem_init = _wrap_semantic_init(
        finroot.memory.semantic.SemanticMemory.__init__,
        str(chroma_dir),
    )

    # 1) Patch the canonical classes' __init__ in place.
    monkeypatch.setattr(
        finroot.memory.digital_twin.DigitalTwinStore,
        "__init__",
        twin_init,
    )
    monkeypatch.setattr(
        finroot.memory.semantic.SemanticMemory,
        "__init__",
        sem_init,
    )

    # 2) Set FINROOT_DIGITAL_TWIN_DB in the parent's env for any subprocess
    #    spawned during this test.  (FINROOT_CHROMA_DIR is intentionally NOT
    #    set here — see docstring above.  The subprocess wrapper handles it.)
    monkeypatch.setenv("FINROOT_DIGITAL_TWIN_DB", str(twin_db))

    # 3) Rebind on the three consumer modules that hold a pre-resolved
    #    reference to the class.  Necessary because the original class is
    #    looked up by name at the module level, not at instantiation time.
    for module_name in (
        "interface.core",
        "finroot.evaluation.harness",
        "finroot.memory.manager",
    ):
        mod = sys.modules.get(module_name)
        if mod is None:
            continue
        if hasattr(mod, "DigitalTwinStore"):
            monkeypatch.setattr(
                mod,
                "DigitalTwinStore",
                finroot.memory.digital_twin.DigitalTwinStore,
            )
        if hasattr(mod, "SemanticMemory"):
            monkeypatch.setattr(
                mod,
                "SemanticMemory",
                finroot.memory.semantic.SemanticMemory,
            )

    # 4) Prevent ``assert_settings`` (called by ``tests/unit/test_config.py``
    #    on a default ``Settings()``) from creating ``data/chroma`` and
    #    ``logs/audit.jsonl`` in the repo root.  The tests only assert the
    #    *result* of ``assert_settings`` (success or ``RuntimeError``), not
    #    the on-disk side effect, so a no-op is safe and keeps the working
    #    tree clean.
    _cfg_modules = [_finroot_config]
    try:
        import src.finroot.utils.config as _src_finroot_config  # noqa: F401

        _cfg_modules.append(_src_finroot_config)
    except ImportError:
        pass
    for _cfg in _cfg_modules:
        monkeypatch.setattr(_cfg, "_ensure_writeable_dir", lambda _path: None)
        monkeypatch.setattr(_cfg, "_ensure_writeable_parent", lambda _path: None)
