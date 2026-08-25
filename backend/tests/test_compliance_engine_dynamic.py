"""Unit tests for compliance.engine dynamic validation engine."""
import pytest
from compliance.engine import (
    ComplianceEngine,
    OverallStatus,
    ValidationStatus,
    get_compliance_engine,
    verify_compliance,
)


def test_sample_input_validation():
    """Test standard sample product data provided in specification."""
    sample_data = {
        "product_name": "ABC Tea",
        "manufacturer_name": "ABC Foods Pvt Ltd",
        "manufacturer_address": "Coimbatore, Tamil Nadu",
        "net_quantity": "500 g",
        "mrp": "₹120",
        "packing_date": "Aug 2026",
        "customer_care": "1800-123-456",
        "country_of_origin": "India",
    }

    report = verify_compliance(sample_data)

    assert "overall_status" in report
    assert "results" in report
    assert "passed" in report
    assert "failed" in report
    assert "warnings" in report
    assert "not_applicable" in report

    assert report["overall_status"] == OverallStatus.COMPLIANT.value
    assert report["failed"] == 0
    assert report["passed"] == 7
    assert report["not_applicable"] == 1  # Country of origin for domestic is NOT_APPLICABLE


def test_domestic_vs_imported_applicability():
    """Verify NOT_APPLICABLE for domestic vs PASS/FAIL for imported products."""
    engine = get_compliance_engine()

    # Domestic product -> Country of origin rule should be NOT_APPLICABLE
    domestic_data = {
        "product_name": "Biscuits",
        "country_of_origin": "India",
    }
    report_dom = engine.validate(domestic_data)
    coo_result_dom = next((r for r in report_dom["results"] if r["rule_id"] == "LM008"), None)
    assert coo_result_dom is not None
    assert coo_result_dom["status"] == ValidationStatus.NOT_APPLICABLE.value

    # Imported product with country of origin -> PASS
    imported_data = {
        "product_name": "Swiss Chocolate",
        "country_of_origin": "Switzerland",
        "is_imported": True,
    }
    report_imp = engine.validate(imported_data)
    coo_result_imp = next((r for r in report_imp["results"] if r["rule_id"] == "LM008"), None)
    assert coo_result_imp is not None
    assert coo_result_imp["status"] == ValidationStatus.PASS.value

    # Imported product missing country of origin -> FAIL
    imported_missing_origin = {
        "product_name": "Imported Coffee",
        "is_imported": True,
    }
    report_imp_fail = engine.validate(imported_missing_origin)
    coo_result_imp_fail = next((r for r in report_imp_fail["results"] if r["rule_id"] == "LM008"), None)
    assert coo_result_imp_fail is not None
    assert coo_result_imp_fail["status"] == ValidationStatus.FAIL.value


def test_validation_types():
    """Test individual validation types (quantity, currency, date, address, contact)."""
    engine = get_compliance_engine()

    # Test Quantity validator
    q_rule = {"rule_id": "T_QTY", "rule_name": "Qty", "field": "net_quantity", "validation_type": "quantity", "mandatory": True}
    assert engine.validate_rule(q_rule, {"net_quantity": "250 ml"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(q_rule, {"net_quantity": "500 g"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(q_rule, {"net_quantity": "100 N"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(q_rule, {"net_quantity": "0 g"})["status"] == ValidationStatus.FAIL.value
    assert engine.validate_rule(q_rule, {"net_quantity": "2 boxes"})["status"] == ValidationStatus.WARNING.value
    assert engine.validate_rule(q_rule, {})["status"] == ValidationStatus.FAIL.value

    # Test Currency validator
    c_rule = {"rule_id": "T_CUR", "rule_name": "Price", "field": "mrp", "validation_type": "currency", "mandatory": True}
    assert engine.validate_rule(c_rule, {"mrp": "₹249.00"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(c_rule, {"mrp": "Rs. 150"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(c_rule, {"mrp": "99.50"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(c_rule, {"mrp": "0"})["status"] == ValidationStatus.FAIL.value
    assert engine.validate_rule(c_rule, {"mrp": "free"})["status"] == ValidationStatus.FAIL.value
    assert engine.validate_rule(c_rule, {})["status"] == ValidationStatus.FAIL.value

    # Test Date validator
    d_rule = {"rule_id": "T_DATE", "rule_name": "Mfg Date", "field": "mfg_date", "validation_type": "date", "mandatory": True}
    assert engine.validate_rule(d_rule, {"mfg_date": "08/2026"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(d_rule, {"mfg_date": "Aug 2026"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(d_rule, {"mfg_date": "15-08-2026"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(d_rule, {"mfg_date": "invalid_date"})["status"] == ValidationStatus.WARNING.value
    assert engine.validate_rule(d_rule, {})["status"] == ValidationStatus.FAIL.value

    # Test Address validator
    a_rule = {"rule_id": "T_ADDR", "rule_name": "Address", "field": "complete_address", "validation_type": "address", "mandatory": True}
    assert engine.validate_rule(a_rule, {"complete_address": "Coimbatore, Tamil Nadu, PIN 641001"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(a_rule, {"complete_address": "Ind"})["status"] == ValidationStatus.WARNING.value
    assert engine.validate_rule(a_rule, {})["status"] == ValidationStatus.FAIL.value

    # Test Contact validator
    cnt_rule = {"rule_id": "T_CNT", "rule_name": "Contact", "field": "customer_care", "validation_type": "contact", "mandatory": True}
    assert engine.validate_rule(cnt_rule, {"customer_care": "1800-123-456"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(cnt_rule, {"customer_care": "support@brand.com"})["status"] == ValidationStatus.PASS.value
    assert engine.validate_rule(cnt_rule, {})["status"] == ValidationStatus.FAIL.value


def test_non_compliant_overall_status():
    """Verify NON_COMPLIANT status when mandatory declarations are missing."""
    incomplete_data = {
        "product_name": "ABC Tea",
        # missing manufacturer, mrp, etc.
    }
    report = verify_compliance(incomplete_data)
    assert report["overall_status"] == OverallStatus.NON_COMPLIANT.value
    assert report["failed"] > 0


def test_extensibility_custom_validator_and_rules():
    """Verify that custom rules and custom validator types can be registered without modifying engine."""
    custom_rules = [
        {
            "rule_id": "CUSTOM001",
            "rule_name": "FSSAI License",
            "field": "fssai_license",
            "mandatory": True,
            "applicable_to": "all",
            "validation_type": "fssai",
            "description": "FSSAI 14-digit license number.",
            "failure_message": "Invalid FSSAI license number.",
            "recommendation": "Print 14 digit FSSAI license.",
            "rule_reference": "FSSAI Reg 2011",
        }
    ]

    custom_engine = ComplianceEngine(rules_data=custom_rules)

    # Register custom validator dynamically
    def validate_fssai(val, rule, ctx):
        if val and str(val).isdigit() and len(str(val)) == 14:
            return ValidationStatus.PASS, f"Valid FSSAI license: {val}", None
        return ValidationStatus.FAIL, rule.get("failure_message"), rule.get("recommendation")

    custom_engine.register_validator("fssai", validate_fssai)

    # Test valid FSSAI
    res_pass = custom_engine.validate({"fssai_license": "10012011000123"})
    assert res_pass["overall_status"] == OverallStatus.COMPLIANT.value
    assert res_pass["passed"] == 1

    # Test invalid FSSAI
    res_fail = custom_engine.validate({"fssai_license": "123"})
    assert res_fail["overall_status"] == OverallStatus.NON_COMPLIANT.value
    assert res_fail["failed"] == 1
