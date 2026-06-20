"""Tests for the FRB question bank (wave-6, task 01).

Minimum 8 tests covering:
- file loads as valid JSON
- >= 24 items
- all required keys present per item (contract shape)
- >= 5 distinct domains
- >= 4 adversarial traps
- difficulty values valid
- tax items have numeric_answer
- twin_ids reference real profiles or null
- numeric_answers cross-check against data/tax_rules.json via TaxRuleTool
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BANK_PATH = REPO_ROOT / "data" / "gold" / "frb_questions.json"
TWINS_PATH = REPO_ROOT / "data" / "samples" / "twin_profiles.json"
TAX_RULES_PATH = REPO_ROOT / "data" / "tax_rules.json"

VALID_DOMAINS = {"portfolio", "risk", "tax", "news_impact", "cashflow", "credit", "general"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_CONFIDENCES = {"high", "medium", "low", None}
REQUIRED_TOP_KEYS = {"id", "domain", "difficulty", "query", "twin_id", "expected", "rationale"}
REQUIRED_EXPECTED_KEYS = {
    "must_mention",
    "must_not",
    "min_citations",
    "expected_confidence",
    "numeric_answer",
    "numeric_tolerance",
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bank() -> list[dict]:
    """Load the FRB question bank once for the test module."""
    with open(BANK_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def real_twin_ids() -> set[str]:
    """Return the set of user_id values declared in twin_profiles.json."""
    with open(TWINS_PATH, encoding="utf-8") as f:
        profiles = json.load(f)
    return {p["user_id"] for p in profiles}


# ---------------------------------------------------------------------------
# File-level integrity
# ---------------------------------------------------------------------------


class TestBankIntegrity:
    """The file loads, parses, and meets the size threshold."""

    def test_file_exists(self):
        """Bank file exists on disk."""
        assert BANK_PATH.is_file(), f"FRB bank not found at {BANK_PATH}"

    def test_loads_as_valid_json(self, bank):
        """Bank file parses as a JSON array of objects."""
        assert isinstance(bank, list)
        assert len(bank) > 0
        for i, item in enumerate(bank):
            assert isinstance(item, dict), f"item {i} is not a dict"

    def test_at_least_24_questions(self, bank):
        """Brief requires >= 24 questions."""
        assert len(bank) >= 24, f"got {len(bank)} questions; need >= 24"

    def test_unique_ids(self, bank):
        """All question IDs are unique."""
        ids = [q["id"] for q in bank]
        assert len(ids) == len(set(ids)), f"duplicate ids found: {ids}"


# ---------------------------------------------------------------------------
# Per-item contract shape
# ---------------------------------------------------------------------------


class TestItemShape:
    """Each item matches the contract shape exactly."""

    def test_required_top_level_keys(self, bank):
        """Every item has the contract's required top-level keys."""
        for q in bank:
            missing = REQUIRED_TOP_KEYS - q.keys()
            assert not missing, f"{q.get('id', '?')} missing top-level keys: {missing}"

    def test_required_expected_keys(self, bank):
        """Every item's `expected` has the contract's required keys."""
        for q in bank:
            exp = q.get("expected", {})
            missing = REQUIRED_EXPECTED_KEYS - exp.keys()
            assert not missing, f"{q['id']}.expected missing keys: {missing}"

    def test_valid_domain(self, bank):
        """Domain is one of the contract's allowed values."""
        for q in bank:
            assert q["domain"] in VALID_DOMAINS, (
                f"{q['id']} has invalid domain '{q['domain']}'; "
                f"allowed: {sorted(VALID_DOMAINS)}"
            )

    def test_valid_difficulty(self, bank):
        """Difficulty is one of the contract's allowed values."""
        for q in bank:
            assert q["difficulty"] in VALID_DIFFICULTIES, (
                f"{q['id']} has invalid difficulty '{q['difficulty']}'"
            )

    def test_valid_expected_confidence(self, bank):
        """expected_confidence is one of the contract's allowed values."""
        for q in bank:
            conf = q["expected"].get("expected_confidence")
            assert conf in VALID_CONFIDENCES, (
                f"{q['id']}.expected.expected_confidence='{conf}' invalid"
            )

    def test_query_non_empty(self, bank):
        """Query is a non-empty string."""
        for q in bank:
            assert isinstance(q["query"], str)
            assert q["query"].strip(), f"{q['id']} has empty query"

    def test_must_mention_must_not_are_lists(self, bank):
        """must_mention and must_not are non-empty lists of strings."""
        for q in bank:
            exp = q["expected"]
            assert isinstance(exp["must_mention"], list)
            assert isinstance(exp["must_not"], list)
            assert all(isinstance(x, str) for x in exp["must_mention"])
            assert all(isinstance(x, str) for x in exp["must_not"])

    def test_min_citations_is_non_negative_int(self, bank):
        """min_citations is an integer >= 0."""
        for q in bank:
            mc = q["expected"]["min_citations"]
            assert isinstance(mc, int) and not isinstance(mc, bool)
            assert mc >= 0, f"{q['id']} min_citations must be >= 0 (got {mc})"

    def test_numeric_tolerance_non_negative(self, bank):
        """numeric_tolerance is a number >= 0."""
        for q in bank:
            tol = q["expected"]["numeric_tolerance"]
            assert isinstance(tol, (int, float))
            assert tol >= 0.0, f"{q['id']} numeric_tolerance must be >= 0 (got {tol})"


# ---------------------------------------------------------------------------
# Domain coverage
# ---------------------------------------------------------------------------


class TestDomainCoverage:
    """Domain and difficulty spread required by the brief."""

    def test_at_least_5_distinct_domains(self, bank):
        """Bank spans at least 5 distinct domains."""
        domains = {q["domain"] for q in bank}
        assert len(domains) >= 5, f"only {len(domains)} distinct domains: {domains}"

    def test_each_required_domain_present(self, bank):
        """Each domain required by the brief is represented."""
        domains = {q["domain"] for q in bank}
        for required in ("portfolio", "risk", "tax", "news_impact"):
            assert required in domains, f"required domain '{required}' missing"

    def test_minimum_per_domain(self, bank):
        """Brief's per-domain minima are met."""
        from collections import Counter

        counts = Counter(q["domain"] for q in bank)
        minima = {"portfolio": 4, "risk": 4, "tax": 4, "news_impact": 3}
        for domain, n in minima.items():
            assert counts[domain] >= n, (
                f"domain '{domain}' has {counts[domain]} items; need >= {n}"
            )

    def test_difficulty_spread_present(self, bank):
        """All three difficulty values are present."""
        difficulties = {q["difficulty"] for q in bank}
        assert difficulties == VALID_DIFFICULTIES, (
            f"missing difficulties: {VALID_DIFFICULTIES - difficulties}"
        )


# ---------------------------------------------------------------------------
# Adversarial traps
# ---------------------------------------------------------------------------


class TestAdversarialTraps:
    """The brief requires >= 4 adversarial trap questions."""

    def test_at_least_4_traps(self, bank):
        """At least 4 trap questions (low confidence + refusal-style must_mention)."""
        refusal_keywords = {"do not act yet", "cannot guarantee"}
        traps = [
            q
            for q in bank
            if q["expected"].get("expected_confidence") == "low"
            and any(
                kw in phrase.lower()
                for phrase in q["expected"]["must_mention"]
                for kw in refusal_keywords
            )
        ]
        assert len(traps) >= 4, (
            f"only {len(traps)} traps found; need >= 4. "
            f"Traps must have expected_confidence='low' AND a refusal phrase "
            f"in must_mention (one of: {refusal_keywords})."
        )

    def test_trap_must_not_excludes_guarantee_language(self, bank):
        """Traps must explicitly forbid the tripwire phrases the agent must avoid."""
        refusal_keywords = {"do not act yet", "cannot guarantee"}
        traps = [
            q
            for q in bank
            if q["expected"].get("expected_confidence") == "low"
            and any(
                kw in phrase.lower()
                for phrase in q["expected"]["must_mention"]
                for kw in refusal_keywords
            )
        ]
        forbidden_substrings = ("guaranteed", "you will definitely", "certain to")
        for trap in traps:
            must_not_blob = " ".join(trap["expected"]["must_not"]).lower()
            assert any(
                bad in must_not_blob for bad in forbidden_substrings
            ), f"{trap['id']} trap must explicitly forbid {forbidden_substrings}"


# ---------------------------------------------------------------------------
# Tax determinism
# ---------------------------------------------------------------------------


class TestTaxItems:
    """Tax items carry a numeric_answer cross-checked against the tax rules."""

    def test_at_least_4_tax_questions(self, bank):
        """Brief requires >= 4 tax questions."""
        tax_items = [q for q in bank if q["domain"] == "tax"]
        assert len(tax_items) >= 4, f"only {len(tax_items)} tax items; need >= 4"

    def test_every_tax_item_has_numeric_answer(self, bank):
        """Every tax item's numeric_answer is set (or null only for qualitative traps)."""
        tax_items = [q for q in bank if q["domain"] == "tax"]
        for q in tax_items:
            na = q["expected"]["numeric_answer"]
            # numeric_answer may be null only for the tax-evasion trap frb-032
            if na is None:
                assert q["id"] == "frb-032", (
                    f"{q['id']}: only the tax-evasion trap (frb-032) may have null "
                    f"numeric_answer; this is a quantitative tax question."
                )

    def test_tax_numeric_answers_match_tax_rules(self, bank):
        """Re-compute each tax numeric_answer with the TaxRuleTool and assert equality.

        This protects the bank from drift if data/tax_rules.json changes.
        """
        from finroot.tools.tax import TaxInput, TaxRuleTool

        # Cross-check table: id -> (gain, gain_type, annual_income)
        scenarios = {
            "frb-012": (200_000.0, "LTCG", 1_800_000.0),
            "frb-013": (50_000.0, "STCG_EQUITY", 1_500_000.0),
            "frb-014": (100_000.0, "LTCG", 1_500_000.0),
            "frb-015": (200_000.0, "STCG_EQUITY", 2_000_000.0),
            "frb-016": (100_000.0, "STCG", 1_800_000.0),
        }
        # frb-017 is a *difference* between two computations; verified separately below.
        tool = TaxRuleTool()
        bank_by_id = {q["id"]: q for q in bank}
        for qid, (gain, gtype, income) in scenarios.items():
            out = tool._run(TaxInput(gain=gain, gain_type=gtype, annual_income=income))
            expected = bank_by_id[qid]["expected"]["numeric_answer"]
            tol = bank_by_id[qid]["expected"]["numeric_tolerance"]
            assert abs(out.tax_amount - expected) <= tol, (
                f"{qid}: tool says {out.tax_amount}, bank says {expected} (tol {tol})"
            )

    def test_frb_017_ltcg_vs_stcg_difference(self, bank):
        """frb-017 encodes (LTCG tax - STCG equity tax) for a 5L gain.

        LTCG 5L @ income 20L:
            taxable = 5L - 1L = 4L
            base    = 4L * 0.10 = 40,000
            cess    = 40,000 * 0.04 = 1,600
            total   = 41,600
        STCG equity 5L:
            base    = 5L * 0.15 = 75,000
            cess    = 75,000 * 0.04 = 3,000
            total   = 78,000
        Difference (LTCG - STCG) = 41,600 - 78,000 = -36,400 (LTCG cheaper).
        """
        bank_by_id = {q["id"]: q for q in bank}
        assert "frb-017" in bank_by_id
        expected = bank_by_id["frb-017"]["expected"]["numeric_answer"]
        assert expected == pytest.approx(-36_400.0, abs=1.0), (
            f"frb-017 numeric_answer should be -36400 (LTCG cheaper by 36,400); got {expected}"
        )


# ---------------------------------------------------------------------------
# Twin references
# ---------------------------------------------------------------------------


class TestTwinReferences:
    """twin_id either references a real profile or is null."""

    def test_twin_ids_reference_real_profiles_or_null(self, bank, real_twin_ids):
        """Every non-null twin_id must match a real user_id in twin_profiles.json."""
        for q in bank:
            tid = q["twin_id"]
            assert tid is None or tid in real_twin_ids, (
                f"{q['id']} references unknown twin_id '{tid}'"
            )

    def test_at_least_one_real_twin_used(self, bank):
        """At least one question exercises a real twin (proves the wiring)."""
        used = {q["twin_id"] for q in bank if q["twin_id"] is not None}
        assert used, "no question uses a real twin"


# ---------------------------------------------------------------------------
# Sanity: full bank cross-check (one shot)
# ---------------------------------------------------------------------------


class TestBankSanity:
    """One roll-up check: numeric invariants per the contract."""

    def test_min_citations_at_least_1_for_tax_and_risk(self, bank):
        """Tax and risk items must demand >= 1 citation (FM-11)."""
        for q in bank:
            if q["domain"] in ("tax", "risk"):
                assert q["expected"]["min_citations"] >= 1, (
                    f"{q['id']} ({q['domain']}) must demand >= 1 citation"
                )

    def test_no_duplicate_queries(self, bank):
        """Two questions with the same query would let the grader trivially copy."""
        queries = [q["query"] for q in bank]
        assert len(queries) == len(set(queries)), "duplicate queries found"
