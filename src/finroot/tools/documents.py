"""DocumentParserTool — regex-based financial document text extraction.

No OCR — caller provides extracted text. Regex patterns per doc_type.
Never raises on parse failure (best-effort tool).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class DocParseInput(BaseModel):
    """Input for document parsing."""

    content: str
    doc_type: Literal["portfolio_statement", "bank_statement", "tax_return", "generic"]

    model_config = {"extra": "forbid"}


class DocParseOutput(BaseModel):
    """Output from document parsing."""

    doc_type: str
    extracted: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    citation: str


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Indian Rupee amounts: ₹1,23,456.78 or Rs 123456.78 or INR 123456
_RUPEE_PATTERN = re.compile(
    r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE
)

# Date patterns: DD/MM/YYYY, DD-MM-YYYY, DD Mon YYYY
_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}\s+"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})\b",
    re.IGNORECASE,
)

# Holdings: TICKER: N units or TICKER x N or TICKER Qty N
_HOLDING_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9&.]{1,15})\b\s*[:xX]\s*(\d+(?:\.\d+)?)\s*(?:units?|shares?|qty)?",
    re.IGNORECASE,
)

# Total value line
_TOTAL_VALUE_PATTERN = re.compile(
    r"(?:total\s+value|portfolio\s+value|net\s+worth)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*"
    r"([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Credits / debits
_CREDITS_PATTERN = re.compile(
    r"(?:total\s+credits?|credits?)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
_DEBITS_PATTERN = re.compile(
    r"(?:total\s+debits?|debits?)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
_CLOSING_BALANCE_PATTERN = re.compile(
    r"(?:closing\s+balance|balance)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Tax fields
_GROSS_INCOME_PATTERN = re.compile(
    r"(?:gross\s+income|total\s+income)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
_TAX_PAID_PATTERN = re.compile(
    r"(?:tax\s+paid|tax\s+payable|total\s+tax)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
_REFUND_PATTERN = re.compile(
    r"(?:refund(?:\s+amount)?)\s*[:\-]?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def _parse_rupee(value: str | None) -> float | None:
    """Parse a rupee string like '1,23,456.78' to float."""
    if value is None:
        return None
    cleaned = value.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_amounts(text: str) -> list[float]:
    """Extract all ₹ amounts from text."""
    amounts: list[float] = []
    for m in _RUPEE_PATTERN.finditer(text):
        val = _parse_rupee(m.group(1))
        if val is not None:
            amounts.append(val)
    return amounts


def _extract_dates(text: str) -> list[str]:
    """Extract dates from text."""
    return [m.group(1) for m in _DATE_PATTERN.finditer(text)]


# ---------------------------------------------------------------------------
# Per doc_type extractors
# ---------------------------------------------------------------------------


def _extract_portfolio(text: str) -> tuple[dict[str, Any], int, int]:
    """Extract from portfolio statement. Returns (data, found, expected)."""
    found = 0
    expected = 3  # total_value, holdings, date
    data: dict[str, Any] = {}

    m = _TOTAL_VALUE_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["total_value"] = val
            found += 1

    holdings: list[dict[str, Any]] = []
    for hm in _HOLDING_PATTERN.finditer(text):
        holdings.append({"ticker": hm.group(1), "units": float(hm.group(2))})
    if holdings:
        data["holdings"] = holdings
        found += 1

    dates = _extract_dates(text)
    if dates:
        data["date"] = dates[0]
        found += 1

    return data, found, expected


def _extract_bank(text: str) -> tuple[dict[str, Any], int, int]:
    """Extract from bank statement. Returns (data, found, expected)."""
    found = 0
    expected = 3  # credits, debits, closing_balance
    data: dict[str, Any] = {}

    m = _CREDITS_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["total_credits"] = val
            found += 1

    m = _DEBITS_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["total_debits"] = val
            found += 1

    m = _CLOSING_BALANCE_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["closing_balance"] = val
            found += 1

    return data, found, expected


def _extract_tax(text: str) -> tuple[dict[str, Any], int, int]:
    """Extract from tax return. Returns (data, found, expected)."""
    found = 0
    expected = 3  # gross_income, tax_paid, refund
    data: dict[str, Any] = {}

    m = _GROSS_INCOME_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["gross_income"] = val
            found += 1

    m = _TAX_PAID_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["tax_paid"] = val
            found += 1

    m = _REFUND_PATTERN.search(text)
    if m:
        val = _parse_rupee(m.group(1))
        if val is not None:
            data["refund_amount"] = val
            found += 1

    return data, found, expected


def _extract_generic(text: str) -> tuple[dict[str, Any], int, int]:
    """Extract any ₹ amounts and dates found."""
    amounts = _extract_amounts(text)
    dates = _extract_dates(text)
    data: dict[str, Any] = {}
    found = 0
    expected = 2  # amounts, dates

    if amounts:
        data["amounts"] = amounts
        found += 1
    if dates:
        data["dates"] = dates
        found += 1

    return data, found, expected


# ---------------------------------------------------------------------------
# DocumentParserTool
# ---------------------------------------------------------------------------


class DocumentParserTool(BaseTool[DocParseInput, DocParseOutput]):
    """Regex-based financial document parser. Never raises on parse failure."""

    name = "document_parser"
    ttl_seconds = 0  # no caching for parse operations

    def _run(self, inp: DocParseInput) -> DocParseOutput:
        extractors = {
            "portfolio_statement": _extract_portfolio,
            "bank_statement": _extract_bank,
            "tax_return": _extract_tax,
            "generic": _extract_generic,
        }

        # Use the requested extractor, fall back to generic for unknown types
        extractor = extractors.get(inp.doc_type, _extract_generic)
        data, found, expected = extractor(inp.content)

        confidence = found / expected if expected > 0 else 0.0
        # Unknown doc_type that's not "generic" still uses generic extractor
        if inp.doc_type not in extractors:
            data, found, expected = _extract_generic(inp.content)
            confidence = found / expected if expected > 0 else 0.0

        return DocParseOutput(
            doc_type=inp.doc_type,
            extracted=data,
            confidence=round(confidence, 4),
            citation=f"Regex extraction from {inp.doc_type} document",
        )


__all__ = [
    "DocParseInput",
    "DocParseOutput",
    "DocumentParserTool",
]
