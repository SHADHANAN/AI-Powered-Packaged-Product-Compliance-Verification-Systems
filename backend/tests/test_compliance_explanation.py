"""Unit tests for compliance.explanation Violation Explanation Engine."""
import pytest
from compliance.explanation import (
    ViolationExplanation,
    ViolationExplanationEngine,
    generate_violation_explanations,
    get_explanation_engine,
)
from compliance.status import ValidationStatus


def test_violation_explanation_for_failure():
    """Verify explanation structure and contents for a FAIL rule (MRP missing)."""
    engine = get_explanation_engine()

    fail_result = {
        "rule_id": "LM005",
        "rule_name": "Maximum Retail Price (MRP)",
        "status": "FAIL",
        "message": "Maximum Retail Price (MRP) declaration is missing or does not explicitly state 'inclusive of all taxes'.",
        "recommendation": "Declare MRP explicitly in the format 'MRP Rs. / ₹ XX.XX (incl. of all taxes)' on the package in accordance with Rule 6(1)(da).",
    }

    explanation = engine.explain_rule_violation(fail_result)

    assert explanation is not None
    assert explanation["rule_id"] == "LM005"
    assert explanation["status"] == "FAIL"
    assert explanation["severity"] == "High"
    assert "MRP" in explanation["violation"]
    assert "Maximum Retail Price" in explanation["explanation"]
    assert "Rule 6(1)(da)" in explanation["rule_reference"]
    assert "Legal Metrology" in explanation["rule_reference"]


def test_violation_explanation_for_warning():
    """Verify explanation generated for a WARNING outcome."""
    engine = get_explanation_engine()

    warning_result = {
        "rule_id": "LM001",
        "rule_name": "Product Generic or Common Name",
        "status": "WARNING",
        "message": "Product Generic or Common Name was detected as 'Green Tea', but OCR confidence (0.55) is below the required threshold (0.75). Manual verification is recommended.",
        "recommendation": "Inspect physical package label to verify text clarity.",
    }

    explanation = engine.explain_rule_violation(warning_result)

    assert explanation is not None
    assert explanation["rule_id"] == "LM001"
    assert explanation["status"] == "WARNING"
    assert "Low OCR Confidence" in explanation["violation"] or "Warning" in explanation["violation"]
    assert "manual" in explanation["explanation"].lower() or "inspection" in explanation["explanation"].lower()


def test_pass_and_not_applicable_are_excluded():
    """Verify PASS and NOT_APPLICABLE results generate no explanations."""
    engine = get_explanation_engine()

    pass_result = {"rule_id": "LM001", "status": "PASS", "message": "Product name valid"}
    na_result = {"rule_id": "LM008", "status": "NOT_APPLICABLE", "message": "Not applicable for domestic"}

    assert engine.explain_rule_violation(pass_result) is None
    assert engine.explain_rule_violation(na_result) is None

    explanations = engine.generate_explanations([pass_result, na_result])
    assert len(explanations) == 0


def test_generate_violation_explanations_batch():
    """Test generating explanations for a batch of mixed results."""
    mixed_results = {
        "results": [
            {"rule_id": "LM001", "status": "PASS"},
            {"rule_id": "LM002", "status": "FAIL", "message": "Manufacturer name missing"},
            {"rule_id": "LM003", "status": "WARNING", "message": "Address is brief with low OCR confidence"},
            {"rule_id": "LM008", "status": "NOT_APPLICABLE"},
        ]
    }

    explanations = generate_violation_explanations(mixed_results)

    assert len(explanations) == 2  # Only FAIL and WARNING
    rule_ids = {e["rule_id"] for e in explanations}
    assert rule_ids == {"LM002", "LM003"}


def test_future_rule_dynamic_support():
    """Verify custom/future rules automatically generate explanations without code changes."""
    custom_rules = [
        {
            "rule_id": "CUSTOM099",
            "rule_name": "E-Waste Disposal Logo",
            "severity": "Medium",
            "description": "Every electronic item package must declare the crossed-out wheeled bin symbol for e-waste disposal.",
            "failure_message": "E-waste disposal symbol is missing.",
            "rule_reference": "E-Waste Management Rules, 2022 Rule 16",
        }
    ]

    custom_engine = ViolationExplanationEngine(rules_data=custom_rules)

    fail_input = {
        "rule_id": "CUSTOM099",
        "status": "FAIL",
        "message": "E-waste disposal symbol is missing.",
    }

    explanation = custom_engine.explain_rule_violation(fail_input)
    assert explanation is not None
    assert explanation["rule_id"] == "CUSTOM099"
    assert explanation["rule_name"] == "E-Waste Disposal Logo"
    assert explanation["severity"] == "Medium"
    assert "E-Waste Management Rules, 2022" in explanation["rule_reference"]
    assert "crossed-out wheeled bin" in explanation["explanation"]
