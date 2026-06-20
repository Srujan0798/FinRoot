"""FinRoot Streamlit entrypoint — auto-detected by Streamlit Community Cloud."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, "src")
os.environ.setdefault("FINROOT_LLM_PROVIDER", "mock")

from interface.ui.app import main

main()
