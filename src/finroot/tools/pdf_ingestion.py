"""PDF statement ingestion tool — auto-build Digital Twin from CAS/AMC statements.

Parses common Indian financial statement formats:
- CDSL CAS (Consolidated Account Statement)
- NSDL CAS
- AMC statements (HDFC, SBI, ICICI, etc.)
- Bank statements (for account balances)

Extracts holdings, account details, and builds a Digital Twin profile.

Note: PDF parsing is inherently fragile. This tool provides a best-effort
extraction with confidence scores and manual override capability.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# I/O types
# ---------------------------------------------------------------------------


class PDFIngestionInput(BaseModel):
    """Input for PDF statement ingestion."""

    pdf_path: str = Field(
        description="Path to the PDF statement file"
    )
    statement_type: str = Field(
        default="auto",
        description="Type of statement: 'cas_cdsl', 'cas_nsdl', 'amc', 'bank', 'auto'",
    )
    user_id: str = Field(
        default="imported",
        description="User ID for the Digital Twin to create/update",
    )
    extract_goals: bool = Field(
        default=False,
        description="Whether to attempt extracting financial goals from the statement",
    )

    model_config = {"extra": "forbid"}


class Holding(BaseModel):
    """A single holding extracted from a statement."""

    symbol: str
    name: str
    asset_class: str  # equity, debt, gold, mutual_fund, etc.
    quantity: float
    unit_price: float
    market_value: float
    currency: str = "INR"
    isin: str | None = None
    folio: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")

    model_config = {"extra": "forbid"}


class PDFIngestionOutput(BaseModel):
    """Output of PDF statement ingestion."""

    holdings: list[Holding]
    account_info: dict[str, Any]
    total_value: float
    statement_type: str
    extraction_confidence: float
    warnings: list[str]
    raw_text_preview: str
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Regex patterns for common Indian statement formats
# ---------------------------------------------------------------------------

# ISIN pattern: 2 letters + 10 alphanumeric
_ISIN_RE = re.compile(r"[A-Z]{2}[A-Z0-9]{10}")

# Folio number pattern
_FOLIO_RE = re.compile(r"(?:Folio|FOLIO)\s*[:.]?\s*(\d+[\w\-/]*)", re.IGNORECASE)

# Quantity patterns
_QTY_RE = re.compile(r"(?:Qty|Quantity|Units|NAV)\s*[:.]?\s*([\d,]+\.?\d*)", re.IGNORECASE)

# Amount patterns (Indian format: 1,23,456.78)
_AMOUNT_RE = re.compile(r"₹?\s*([\d,]+\.?\d*)")

# PAN pattern
_PAN_RE = re.compile(r"[A-Z]{5}\d{4}[A-Z]")

# Date patterns
_DATE_RE = re.compile(r"(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class PDFIngestionTool(BaseTool[PDFIngestionInput, PDFIngestionOutput]):
    """Extract holdings from PDF statements and build a Digital Twin.

    Supports:
    - CDSL/NSDL Consolidated Account Statement (CAS)
    - AMC mutual fund statements
    - Bank statements (for balances)

    The tool uses regex-based extraction for robustness. For complex PDFs,
    it falls back to raw text extraction with confidence scoring.
    """

    name = "pdf_ingestion"

    def __init__(self, audit: Any = None, mock: bool = False) -> None:
        super().__init__(audit=audit)
        self.mock = mock

    def _run(self, inp: PDFIngestionInput) -> PDFIngestionOutput:
        pdf_path = Path(inp.pdf_path)

        if not pdf_path.exists():
            raise ToolCallError(f"PDF file not found: {inp.pdf_path}")

        if not pdf_path.suffix.lower() == ".pdf":
            raise ToolCallError(f"File is not a PDF: {inp.pdf_path}")

        # Extract text from PDF
        raw_text = self._extract_text(pdf_path)

        # Detect statement type if auto
        stmt_type = inp.statement_type
        if stmt_type == "auto":
            stmt_type = self._detect_statement_type(raw_text)

        # Parse based on statement type
        if stmt_type == "cas_cdsl":
            holdings, account_info = self._parse_cdsl_cas(raw_text)
        elif stmt_type == "cas_nsdl":
            holdings, account_info = self._parse_nsdl_cas(raw_text)
        elif stmt_type == "amc":
            holdings, account_info = self._parse_amc_statement(raw_text)
        elif stmt_type == "bank":
            holdings, account_info = self._parse_bank_statement(raw_text)
        else:
            # Generic extraction
            holdings, account_info = self._parse_generic(raw_text)

        # Calculate totals
        total_value = sum(h.market_value for h in holdings)

        # Calculate overall confidence
        avg_confidence = sum(h.confidence for h in holdings) / len(holdings) if holdings else 0.0

        # Generate warnings
        warnings = self._generate_warnings(holdings, stmt_type, raw_text)

        # Build citation
        citation = (
            f"Extracted {len(holdings)} holdings from {stmt_type} statement. "
            f"Total value: ₹{total_value:,.2f}. "
            f"Extraction confidence: {avg_confidence:.1%}. "
            f"Source: {pdf_path.name}"
        )

        return PDFIngestionOutput(
            holdings=holdings,
            account_info=account_info,
            total_value=round(total_value, 2),
            statement_type=stmt_type,
            extraction_confidence=round(avg_confidence, 3),
            warnings=warnings,
            raw_text_preview=raw_text[:1000],
            citation=citation,
        )

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF. Uses PyPDF2 if available, falls back to basic extraction."""
        try:
            import PyPDF2

            text_parts: list[str] = []
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("PyPDF2 not available — using basic text extraction")
            # Try pdftotext if available
            try:
                import subprocess

                result = subprocess.run(
                    ["pdftotext", str(pdf_path), "-"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return result.stdout
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            # Return placeholder for mock mode
            if self.mock:
                return self._mock_pdf_text()
            raise ToolCallError(
                "PDF extraction requires PyPDF2 or pdftotext. "
                "Install with: pip install PyPDF2"
            ) from None

    def _detect_statement_type(self, text: str) -> str:
        """Auto-detect the type of financial statement."""
        text_lower = text.lower()

        if "cdsl" in text_lower or "central depository" in text_lower:
            return "cas_cdsl"
        elif "nsdl" in text_lower or "national securities depository" in text_lower:
            return "cas_nsdl"
        elif any(amc in text_lower for amc in ["hdfc mutual fund", "sbi mutual fund", "icici prudential"]):
            return "amc"
        elif any(bank in text_lower for bank in ["savings account", "current account", "bank statement"]):
            return "bank"
        else:
            return "generic"

    def _parse_cdsl_cas(self, text: str) -> tuple[list[Holding], dict[str, Any]]:
        """Parse CDSL Consolidated Account Statement."""
        holdings: list[Holding] = []
        account_info: dict[str, Any] = {}

        # Extract PAN
        pan_match = _PAN_RE.search(text)
        if pan_match:
            account_info["pan"] = pan_match.group()

        # Extract holdings using ISIN pattern
        lines = text.split("\n")
        for i, line in enumerate(lines):
            isin_match = _ISIN_RE.search(line)
            if isin_match:
                isin = isin_match.group()
                # Try to extract quantity and price from nearby lines
                context = " ".join(lines[max(0, i - 1):min(len(lines), i + 3)])
                qty_match = _QTY_RE.search(context)
                amount_match = _AMOUNT_RE.search(context)

                qty = self._parse_number(qty_match.group(1)) if qty_match else 0
                price = self._parse_number(amount_match.group(1)) if amount_match else 0

                # Extract name (typically before ISIN)
                name_match = re.search(r"([A-Z][A-Za-z\s&]+?)(?:\s+ISIN|\s+" + isin + ")", line)
                name = name_match.group(1).strip() if name_match else f"Holding {isin}"

                holdings.append(Holding(
                    symbol=isin,
                    name=name,
                    asset_class=self._classify_asset(name, isin),
                    quantity=qty,
                    unit_price=price / qty if qty > 0 and price > 0 else price,
                    market_value=price,
                    isin=isin,
                    confidence=0.7 if qty > 0 else 0.3,
                ))

        return holdings, account_info

    def _parse_nsdl_cas(self, text: str) -> tuple[list[Holding], dict[str, Any]]:
        """Parse NSDL Consolidated Account Statement."""
        # Similar to CDSL but with different format
        return self._parse_cdsl_cas(text)  # Reuse CDSL parser for now

    def _parse_amc_statement(self, text: str) -> tuple[list[Holding], dict[str, Any]]:
        """Parse AMC mutual fund statement."""
        holdings: list[Holding] = []
        account_info: dict[str, Any] = {}

        # Extract folio number
        folio_match = _FOLIO_RE.search(text)
        if folio_match:
            account_info["folio"] = folio_match.group(1)

        # Look for scheme names and NAV
        lines = text.split("\n")
        for i, line in enumerate(lines):
            # Common AMC patterns
            scheme_match = re.search(
                r"([A-Z][A-Za-z\s]+(?:Fund|Plan|Option|Growth|Direct))", line
            )
            if scheme_match:
                scheme_name = scheme_match.group(1).strip()
                context = " ".join(lines[max(0, i - 1):min(len(lines), i + 3)])

                # Extract units and NAV
                units_match = re.search(r"(?:Units|Balance)\s*[:.]?\s*([\d,]+\.?\d*)", context, re.IGNORECASE)
                nav_match = re.search(r"NAV\s*[:.]?\s*₹?([\d,]+\.?\d*)", context, re.IGNORECASE)

                units = self._parse_number(units_match.group(1)) if units_match else 0
                nav = self._parse_number(nav_match.group(1)) if nav_match else 0

                market_value = units * nav if units > 0 and nav > 0 else 0

                holdings.append(Holding(
                    symbol=scheme_name[:20].upper().replace(" ", ""),
                    name=scheme_name,
                    asset_class="mutual_fund",
                    quantity=units,
                    unit_price=nav,
                    market_value=market_value,
                    folio=folio_match.group(1) if folio_match else None,
                    confidence=0.6 if units > 0 else 0.3,
                ))

        return holdings, account_info

    def _parse_bank_statement(self, text: str) -> tuple[list[Holding], dict[str, Any]]:
        """Parse bank statement for account balance."""
        holdings: list[Holding] = []
        account_info: dict[str, Any] = {}

        # Extract account number
        acct_match = re.search(r"(?:A/c|Account)\s*(?:No\.?)?\s*[:.]?\s*(\d+)", text, re.IGNORECASE)
        if acct_match:
            account_info["account_number"] = acct_match.group(1)

        # Extract balance
        balance_match = re.search(r"(?:Balance|Closing Balance)\s*[:.]?\s*₹?([\d,]+\.?\d*)", text, re.IGNORECASE)
        if balance_match:
            balance = self._parse_number(balance_match.group(1))
            holdings.append(Holding(
                symbol="BANK_BALANCE",
                name="Bank Savings Account",
                asset_class="cash",
                quantity=1,
                unit_price=balance,
                market_value=balance,
                confidence=0.8,
            ))

        return holdings, account_info

    def _parse_generic(self, text: str) -> tuple[list[Holding], dict[str, Any]]:
        """Generic extraction for unknown statement formats."""
        holdings: list[Holding] = []
        account_info: dict[str, Any] = {}

        # Try to find any ISINs
        isins = _ISIN_RE.findall(text)
        for isin in set(isins):
            holdings.append(Holding(
                symbol=isin,
                name=f"Holding {isin}",
                asset_class="unknown",
                quantity=0,
                unit_price=0,
                market_value=0,
                isin=isin,
                confidence=0.2,
            ))

        return holdings, account_info

    def _classify_asset(self, name: str, isin: str = "") -> str:
        """Classify asset based on name and ISIN."""
        name_lower = name.lower()

        if any(kw in name_lower for kw in ["equity", "share", "stock", "inf", "ine"]):
            return "equity"
        elif any(kw in name_lower for kw in ["bond", "debenture", "gsec", "t-bill", "govt"]):
            return "debt"
        elif any(kw in name_lower for kw in ["gold", "silver", "commodity"]):
            return "commodity"
        elif any(kw in name_lower for kw in ["mutual", "fund", "etf", "index"]):
            return "mutual_fund"
        elif isin.startswith("IN"):
            return "equity"  # Indian ISINs are typically equity
        else:
            return "unknown"

    def _parse_number(self, s: str) -> float:
        """Parse Indian number format (1,23,456.78)."""
        try:
            return float(s.replace(",", ""))
        except (ValueError, AttributeError):
            return 0.0

    def _generate_warnings(
        self, holdings: list[Holding], stmt_type: str, text: str
    ) -> list[str]:
        """Generate warnings about the extraction."""
        warnings: list[str] = []

        if not holdings:
            warnings.append("No holdings could be extracted from the statement.")

        low_confidence = [h for h in holdings if h.confidence < 0.5]
        if low_confidence:
            warnings.append(
                f"{len(low_confidence)} holdings have low extraction confidence. "
                "Manual verification recommended."
            )

        zero_value = [h for h in holdings if h.market_value <= 0]
        if zero_value:
            warnings.append(
                f"{len(zero_value)} holdings have zero market value. "
                "Prices may not have been extracted."
            )

        if stmt_type == "generic":
            warnings.append(
                "Statement type could not be determined. "
                "Extraction may be incomplete."
            )

        return warnings

    def _mock_pdf_text(self) -> str:
        """Return mock PDF text for testing."""
        return """
        CONSOLIDATED ACCOUNT STATEMENT
        CDSL - Central Depository Services (India) Limited

        PAN: ABCDE1234F
        Account Statement for the period 01-Apr-2025 to 31-Mar-2026

        HOLDINGS:
        ISIN: INF200K01VZ3  HDFC Equity Fund - Growth Plan
        Qty: 1,234.567  NAV: 85.23  Value: 1,05,234.56

        ISIN: INF109K01VZ1  SBI Blue Chip Fund - Direct Growth
        Qty: 2,345.678  NAV: 65.45  Value: 1,53,456.78

        ISIN: INE002A01018  Reliance Industries Ltd
        Qty: 100  Price: 2,456.78  Value: 2,45,678.00

        ISIN: INE009A01021  Infosys Ltd
        Qty: 50  Price: 1,567.89  Value: 78,394.50

        TOTAL PORTFOLIO VALUE: ₹5,82,763.84
        """


# ---------------------------------------------------------------------------
# Helper to build Digital Twin from ingestion
# ---------------------------------------------------------------------------


def build_twin_from_ingestion(
    output: PDFIngestionOutput,
    user_id: str = "imported",
    name: str = "Imported User",
    age: int = 30,
) -> dict[str, Any]:
    """Build a Digital Twin dict from ingestion output.

    Returns a dict that can be validated into a DigitalTwin model.
    """

    now = datetime.now(UTC)

    holdings = []
    for h in output.holdings:
        holdings.append({
            "symbol": h.symbol,
            "name": h.name,
            "asset_class": h.asset_class,
            "quantity": h.quantity,
            "unit_price": h.unit_price,
            "market_value": h.market_value,
            "currency": h.currency,
            "isin": h.isin,
            "folio": h.folio,
        })

    return {
        "user_id": user_id,
        "name": name,
        "age": age,
        "risk_tolerance": "moderate",
        "investment_horizon": "medium",
        "monthly_income": 0.0,
        "monthly_expenses": 0.0,
        "tax_bracket_pct": 30.0,
        "goals": [],
        "constraints": [],
        "holdings": holdings,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


__all__ = [
    "PDFIngestionTool",
    "PDFIngestionInput",
    "PDFIngestionOutput",
    "Holding",
    "build_twin_from_ingestion",
]
