"""Automated Compliance Test Suite Runner.

Dynamically loads and validates all JSON dataset test cases under tests/compliance/*.json
against the Compliance Engine, Scoring Engine, and Explanation/Recommendation modules.
"""
import json
from pathlib import Path
import pytest
from compliance.engine import get_compliance_engine

COMPLIANCE_DATASETS_DIR = Path(__file__).parent / "compliance"


def load_all_compliance_test_cases():
    """Discover and parse all JSON test files in tests/compliance/."""
    test_cases = []
    json_files = sorted(COMPLIANCE_DATASETS_DIR.glob("*.json"))

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cases = data.get("test_cases", [])
        for case in cases:
            case_id = case.get("case_id", file_path.stem)
            test_cases.append((file_path.name, case_id, case))

    return test_cases


TEST_CASES = load_all_compliance_test_cases()


@pytest.mark.parametrize("dataset_file,case_id,case_data", TEST_CASES, ids=[f"{f}::{cid}" for f, cid, _ in TEST_CASES])
def test_compliance_dataset_scenario(dataset_file, case_id, case_data):
    """Execute each dataset scenario through the Compliance Engine and verify all expectations."""
    engine = get_compliance_engine()

    input_data = case_data.get("input", {})
    context = case_data.get("context")
    expected = case_data.get("expected", {})

    report = engine.validate(input_data, context=context)

    # 1. Verify Overall Status if specified
    if "overall_status" in expected:
        assert report["overall_status"] == expected["overall_status"], (
            f"[{case_id}] Expected overall_status '{expected['overall_status']}', got '{report['overall_status']}'"
        )

    # 2. Verify Compliance Score if specified
    if "compliance_score" in expected:
        assert report["compliance_score"] == expected["compliance_score"], (
            f"[{case_id}] Expected compliance_score '{expected['compliance_score']}', got '{report['compliance_score']}'"
        )

    # 3. Verify Risk Level if specified
    if "risk_level" in expected:
        assert report["risk_level"] == expected["risk_level"], (
            f"[{case_id}] Expected risk_level '{expected['risk_level']}', got '{report['risk_level']}'"
        )

    # 4. Verify Failure/Warning counts if specified
    if "failed" in expected:
        assert report["failed"] == expected["failed"], (
            f"[{case_id}] Expected failed count '{expected['failed']}', got '{report['failed']}'"
        )
    if "warnings" in expected:
        assert report["warnings"] == expected["warnings"], (
            f"[{case_id}] Expected warnings count '{expected['warnings']}', got '{report['warnings']}'"
        )
    if "passed" in expected:
        assert report["passed"] == expected["passed"], (
            f"[{case_id}] Expected passed count '{expected['passed']}', got '{report['passed']}'"
        )
    if "not_applicable" in expected:
        assert report["not_applicable"] == expected["not_applicable"], (
            f"[{case_id}] Expected not_applicable count '{expected['not_applicable']}', got '{report['not_applicable']}'"
        )

    # 5. Verify individual Rule Statuses
    if "rule_statuses" in expected:
        results_by_id = {r["rule_id"]: r["status"] for r in report["results"]}
        for rule_id, exp_status in expected["rule_statuses"].items():
            assert rule_id in results_by_id, f"[{case_id}] Rule '{rule_id}' missing in validation results"
            actual_status = results_by_id[rule_id]
            assert actual_status == exp_status, (
                f"[{case_id}] Rule '{rule_id}' expected status '{exp_status}', got '{actual_status}'"
            )
