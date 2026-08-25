"""Tests for compliance.status module and intelligent 4-state rule evaluation."""
import pytest
from compliance.status import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    OverallStatus,
    RuleEvaluationResult,
    StatusEvaluator,
    ValidationStatus,
)
from compliance.engine import ComplianceEngine, get_compliance_engine, verify_compliance


def test_validation_statuses_enum():
    """Verify all four statuses are properly defined."""
    assert ValidationStatus.PASS.value == "PASS"
    assert ValidationStatus.WARNING.value == "WARNING"
    assert ValidationStatus.FAIL.value == "FAIL"
    assert ValidationStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"


def test_rule_evaluation_result_serialization():
    """Test RuleEvaluationResult to_dict serialization."""
    res = RuleEvaluationResult(
        rule_id="LM001",
        rule_name="Product Name",
        status=ValidationStatus.PASS,
        message="Valid product name",
        recommendation=None,
    )
    d = res.to_dict()
    assert d["rule_id"] == "LM001"
    assert d["status"] == "PASS"
    assert d["message"] == "Valid product name"


def test_overall_status_calculation():
    """Test aggregation logic for overall compliance status."""
    # All pass -> COMPLIANT
    assert StatusEvaluator.calculate_overall_status(passed=7, failed=0, warnings=0, not_applicable=1) == OverallStatus.COMPLIANT

    # Any failure -> NON_COMPLIANT
    assert StatusEvaluator.calculate_overall_status(passed=6, failed=1, warnings=0, not_applicable=1) == OverallStatus.NON_COMPLIANT
    assert StatusEvaluator.calculate_overall_status(passed=5, failed=2, warnings=1, not_applicable=0) == OverallStatus.NON_COMPLIANT

    # No failures, but warnings present -> PARTIALLY_COMPLIANT
    assert StatusEvaluator.calculate_overall_status(passed=6, failed=0, warnings=1, not_applicable=1) == OverallStatus.PARTIALLY_COMPLIANT


def test_ocr_confidence_triggers_warning():
    """Verify low OCR confidence causes a PASS to become a WARNING with manual review recommended."""
    engine = ComplianceEngine(confidence_threshold=0.75)

    # High confidence -> PASS
    high_conf_data = {
        "product_name": {"value": "Organic Green Tea", "confidence": 0.95},
        "manufacturer_name": "Tea Estates Ltd",
        "manufacturer_address": "Assam, India",
        "net_quantity": "250 g",
        "mrp": "Rs. 250",
        "mfg_date": "08/2026",
        "customer_care": "1800-111-222",
        "country_of_origin": "India",
    }
    report_high = engine.validate(high_conf_data)
    p_name_res = next(r for r in report_high["results"] if r["rule_id"] == "LM001")
    assert p_name_res["status"] == ValidationStatus.PASS.value

    # Low confidence (< 0.75) -> WARNING
    low_conf_data = {
        "product_name": {"value": "Organic Green Tea", "confidence": 0.52},
        "manufacturer_name": "Tea Estates Ltd",
        "manufacturer_address": "Assam, India",
        "net_quantity": "250 g",
        "mrp": {"value": "Rs. 250", "confidence": 0.48},
        "mfg_date": "08/2026",
        "customer_care": "1800-111-222",
        "country_of_origin": "India",
    }
    report_low = engine.validate(low_conf_data)
    p_name_res_low = next(r for r in report_low["results"] if r["rule_id"] == "LM001")
    assert p_name_res_low["status"] == ValidationStatus.WARNING.value
    assert "OCR confidence (0.52) is below" in p_name_res_low["message"]
    assert report_low["warnings"] == 2
    assert report_low["overall_status"] == OverallStatus.PARTIALLY_COMPLIANT.value
    assert report_low["risk_level"] == "MEDIUM"


def test_context_confidence_threshold_override():
    """Verify confidence threshold can be configured per validation request via context."""
    engine = get_compliance_engine()

    data = {
        "product_name": "Organic Honey",
        "manufacturer_name": "Bee Farm Ltd",
        "complete_address": "Shimla, Himachal Pradesh",
        "net_quantity": "500 g",
        "mrp": "₹350",
        "mfg_date": "09/2026",
        "customer_care": "care@beefarm.com",
    }
    # With confidence 0.60 and strict threshold 0.85 -> WARNING
    context = {
        "confidence_threshold": 0.85,
        "confidences": {"mrp": 0.60},
    }
    report = engine.validate(data, context=context)
    mrp_res = next(r for r in report["results"] if r["rule_id"] == "LM005")
    assert mrp_res["status"] == ValidationStatus.WARNING.value
    assert "below the required threshold (0.85)" in mrp_res["message"]


def test_unreadable_ocr_artifacts_triggers_warning():
    """Verify text containing garbled characters returns WARNING."""
    evaluator = StatusEvaluator()
    rule = {"rule_id": "LM001", "rule_name": "Product Name"}

    status, msg, rec = evaluator.evaluate_status(
        base_status=ValidationStatus.PASS,
        base_message="Product Name declared",
        base_recommendation=None,
        field_value="Te~a §± Prod^uct",
        confidence=0.90,
        rule=rule,
    )
    assert status == ValidationStatus.WARNING
    assert "unreadable OCR artifacts" in msg
