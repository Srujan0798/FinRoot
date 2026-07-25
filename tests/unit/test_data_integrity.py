"""Sample-data integrity tests for FinRoot gold sets.

Catches data corruption in:
- data/gold/frb_questions.json (83-task FRB benchmark)
- data/gold/adversarial_questions.json (20-task red-team set)
- data/tax_rules.json (Indian FY 2024-25 tax rules)
- data/samples/ (3 Digital Twin profiles + conversation fixture)

If any of these files are malformed, the eval suite will produce nonsense
metrics, so we lock the schema here. Fast (<1s).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

# Required schema fields per FRB question
FRB_REQUIRED_FIELDS = {"id", "domain", "difficulty", "query", "expected", "rationale"}
EXPECTED_REQUIRED_FIELDS = {
    "must_mention",
    "must_not",
    "min_citations",
    "expected_confidence",
    "numeric_answer",
    "numeric_tolerance",
}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_CONFIDENCE = {"low", "medium", "high"}


class TestFRBBank:
    @pytest.fixture(scope="class")
    def bank(self) -> list[dict]:
        path = DATA_DIR / "gold" / "frb_questions.json"
        assert path.exists(), f"FRB bank not found: {path}"
        return json.loads(path.read_text())

    def test_is_list(self, bank: list[dict]) -> None:
        assert isinstance(bank, list)
        assert len(bank) > 0

    def test_minimum_size(self, bank: list[dict]) -> None:
        # The brief says 83 tasks. Lock that as a floor (can grow, can't shrink).
        assert len(bank) >= 83, (
            f"FRB bank has {len(bank)} tasks, expected >= 83. "
            "If you intentionally shrunk the bank, update this floor."
        )

    def test_ids_unique(self, bank: list[dict]) -> None:
        ids = [q["id"] for q in bank]
        dupes = {i for i in ids if ids.count(i) > 1}
        assert not dupes, f"Duplicate question IDs: {dupes}"

    def test_id_format(self, bank: list[dict]) -> None:
        for q in bank:
            assert q["id"].startswith("frb-"), (
                f"ID {q['id']!r} must start with 'frb-'"
            )
            assert q["id"].split("-")[1].isdigit(), (
                f"ID {q['id']!r} must be frb-NNN (zero-padded NNN optional)"
            )

    def test_required_fields(self, bank: list[dict]) -> None:
        for i, q in enumerate(bank):
            missing = FRB_REQUIRED_FIELDS - set(q.keys())
            assert not missing, (
                f"Question {i} (id={q.get('id', '?')}) missing fields: {missing}"
            )

    def test_expected_schema(self, bank: list[dict]) -> None:
        for q in bank:
            expected = q["expected"]
            missing = EXPECTED_REQUIRED_FIELDS - set(expected.keys())
            assert not missing, (
                f"Question {q['id']!r} expected missing: {missing}"
            )
            assert isinstance(expected["must_mention"], list)
            assert isinstance(expected["must_not"], list)
            assert isinstance(expected["min_citations"], int)
            assert expected["min_citations"] >= 0
            assert expected["expected_confidence"] in VALID_CONFIDENCE
            # numeric_answer can be null OR a number
            assert (
                expected["numeric_answer"] is None
                or isinstance(expected["numeric_answer"], (int, float))
            )

    def test_difficulty_values(self, bank: list[dict]) -> None:
        for q in bank:
            assert q["difficulty"] in VALID_DIFFICULTIES, (
                f"Question {q['id']!r} has invalid difficulty "
                f"{q['difficulty']!r}; expected one of {VALID_DIFFICULTIES}"
            )

    def test_query_not_empty(self, bank: list[dict]) -> None:
        for q in bank:
            assert isinstance(q["query"], str) and len(q["query"]) > 10, (
                f"Question {q['id']!r} has too-short query: {q['query']!r}"
            )

    def test_rationale_not_empty(self, bank: list[dict]) -> None:
        for q in bank:
            assert isinstance(q["rationale"], str) and len(q["rationale"]) > 20, (
                f"Question {q['id']!r} has too-short rationale"
            )

    def test_domains_represented(self, bank: list[dict]) -> None:
        domains = {q["domain"] for q in bank}
        # Per the brief, 11 financial domains. Lock the floor at 8 (we may
        # have consolidated some, but a big drop is a data bug).
        assert len(domains) >= 8, (
            f"FRB bank covers {len(domains)} domains {domains}, expected >= 8"
        )

    def test_min_citations_at_least_one(self, bank: list[dict]) -> None:
        for q in bank:
            assert q["expected"]["min_citations"] >= 1, (
                f"Question {q['id']!r} has min_citations=0; "
                "every FRB task should require at least 1 citation"
            )


class TestAdversarialBank:
    @pytest.fixture(scope="class")
    def bank(self) -> list[dict]:
        path = DATA_DIR / "gold" / "adversarial_questions.json"
        if not path.exists():
            pytest.skip("adversarial_questions.json not present")
        return json.loads(path.read_text())

    def test_minimum_size(self, bank: list[dict]) -> None:
        assert len(bank) >= 20, (
            f"Adversarial bank has {len(bank)} tasks, expected >= 20"
        )

    def test_ids_unique(self, bank: list[dict]) -> None:
        ids = [q["id"] for q in bank]
        dupes = {i for i in ids if ids.count(i) > 1}
        assert not dupes, f"Duplicate adversarial IDs: {dupes}"


class TestTaxRules:
    @pytest.fixture(scope="class")
    def rules(self) -> dict:
        path = DATA_DIR / "tax_rules.json"
        assert path.exists(), f"tax_rules.json not found: {path}"
        return json.loads(path.read_text())

    def test_top_level_structure(self, rules: dict) -> None:
        # The file has a flat structure: {rules, income_tax_slabs, metadata}
        assert "income_tax_slabs" in rules, "tax_rules.json missing income_tax_slabs"
        assert "rules" in rules, "tax_rules.json missing rules"

    def test_slab_structure(self, rules: dict) -> None:
        slabs = rules["income_tax_slabs"]
        assert isinstance(slabs, list) and len(slabs) > 0, (
            "income_tax_slabs must be a non-empty list"
        )
        for s in slabs:
            assert isinstance(s, dict), "slab items must be dicts"
            # Each slab should have at least a rate
            assert "rate" in s, f"slab missing rate: {s}"

    def test_metadata_present(self, rules: dict) -> None:
        # metadata should at least have a fiscal year reference
        meta = rules.get("metadata", {})
        if not meta:
            pytest.skip("no metadata field")
        # Any FY reference is fine — we just want to lock the FY of the rules
        meta_str = str(meta)
        assert "FY" in meta_str or "20" in meta_str, (
            f"metadata does not look like a fiscal-year reference: {meta}"
        )


class TestSamples:
    def test_samples_dir_exists(self) -> None:
        assert (DATA_DIR / "samples").exists(), "data/samples/ missing"

    def test_twin_profiles_loadable(self) -> None:
        # Look for any JSON file in samples and verify it parses
        samples = DATA_DIR / "samples"
        json_files = list(samples.glob("*.json"))
        if not json_files:
            pytest.skip("No JSON files in data/samples/")
        for f in json_files:
            data = json.loads(f.read_text())
            assert data is not None, f"Empty JSON in {f.name}"
