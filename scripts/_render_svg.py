#!/usr/bin/env python3
"""Fallback SVG renderer for architecture diagram when mmdc and mermaid-py fail.

Usage: python3 _render_svg.py <input.mmd> <output.svg>
"""
from __future__ import annotations

import base64
import sys
import urllib.request
from pathlib import Path


def render_via_mermaid_ink(mmd_path: Path, svg_path: Path) -> None:
    """Render a .mmd file to SVG via the free mermaid.ink API."""
    raw = mmd_path.read_text()
    # Strip comments
    lines = [line for line in raw.splitlines() if not line.strip().startswith("%%")]
    clean = "\n".join(lines).strip()
    encoded = base64.urlsafe_b64encode(clean.encode()).decode()
    url = f"https://mermaid.ink/svg/{encoded}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        svg_data = resp.read()
    svg_path.write_bytes(svg_data)


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.mmd> <output.svg>", file=sys.stderr)
        sys.exit(1)
    mmd_path = Path(sys.argv[1])
    svg_path = Path(sys.argv[2])
    if not mmd_path.exists():
        print(f"ERROR: {mmd_path} not found", file=sys.stderr)
        sys.exit(1)
    render_via_mermaid_ink(mmd_path, svg_path)


if __name__ == "__main__":
    main()
