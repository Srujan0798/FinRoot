"""Dark finance theme for FinRoot Streamlit UI.

Provides ``apply_theme()`` which returns a CSS string to inject, plus badge
helpers for confidence and risk bands.

Writes: ``src/interface/ui/theme.py`` (wave-7, task 02).
"""

from __future__ import annotations

# -- Colour palette -----------------------------------------------------------

BG_DARK = "#0B0E14"
BG_NAVY = "#11151C"
CARD_BG = "#161B22"
GREEN = "#3FB950"
RED = "#F85149"
ACCENT = "#58A6FF"
TEXT_MUTED = "#8B949E"
TEXT_DEFAULT = "#E6EDF3"
MONO_FONT = "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"

_CSS = f"""
<style>
/* ---- base ---- */
.stApp, .main .block-container {{
    background-color: {BG_DARK} !important;
    color: {TEXT_DEFAULT};
}}
header[data-testid="stHeader"] {{
    background-color: {BG_NAVY} !important;
}}

/* ---- sidebar ---- */
section[data-testid="stSidebar"] {{
    background-color: {BG_NAVY};
}}

/* ---- cards / containers ---- */
div[data-testid="stExpander"],
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: #30363D !important;
}}

/* ---- monospace numbers ---- */
.finroot-mono {{
    font-family: {MONO_FONT};
}}

/* ---- tag badges ---- */
.finroot-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    line-height: 1.4;
}}
</style>
"""


def apply_theme() -> str:
    """Return the CSS string to inject via ``st.markdown(..., unsafe_allow_html=True)``."""
    return _CSS


# -- Badge helpers ------------------------------------------------------------


def confidence_badge(label: str) -> str:
    """Return an HTML chip showing a confidence level (e.g. HIGH, MEDIUM, LOW)."""
    upper = label.strip().upper()
    colour_map: dict[str, str] = {
        "HIGH": GREEN,
        "MEDIUM": ACCENT,
        "LOW": RED,
        "VERY HIGH": GREEN,
        "VERY LOW": RED,
    }
    bg = colour_map.get(upper, ACCENT)
    return (
        f'<span class="finroot-badge" '
        f'style="background-color: {bg}22; color: {bg}; border: 1px solid {bg}55;">'
        f"{upper}</span>"
    )


def risk_badge(band: str) -> str:
    """Return an HTML chip showing a risk band (e.g. Conservative, Aggressive)."""
    upper = band.strip().upper()
    colour_map: dict[str, str] = {
        "CONSERVATIVE": GREEN,
        "MODERATE": ACCENT,
        "AGGRESSIVE": RED,
        "HIGH": RED,
        "LOW": GREEN,
    }
    bg = colour_map.get(upper, ACCENT)
    return (
        f'<span class="finroot-badge" '
        f'style="background-color: {bg}22; color: {bg}; border: 1px solid {bg}55;">'
        f"{band.strip()}</span>"
    )


__all__ = ["apply_theme", "confidence_badge", "risk_badge"]
