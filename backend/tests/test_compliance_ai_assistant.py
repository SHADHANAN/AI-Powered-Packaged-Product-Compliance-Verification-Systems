"""Unit tests for the AI Compliance Assistant module."""
import pytest
from compliance.ai_assistant import (
    AIComplianceAssistant,
    ask_compliance_assistant,
    generate_compliance_summary,
)
from compliance.engine import get_compliance_engine


@pytest.fixture
def non_compliant_report():
    """Generate a report for a product missing MRP and having invalid unit."""
    engine = get_compliance_engine()
    data = {
        "product_name": "Premium Cashews",
        "manufacturer_name": "Nut Co Ltd",
        "complete_address": "Kochi, Kerala 682001",
        "net_quantity": "2 packets",
        "mfg_date": "08/2026",
        "customer_care": "care@nutco.in",
        "country_of_origin": "India",
    }
    return engine.validate(data)


@pytest.fixture
def compliant_report():
    """Generate a report for a fully compliant domestic product."""
    engine = get_compliance_engine()
    data = {
        "product_name": "Tata Tea Gold",
        "manufacturer_name": "Tata Consumer Products Ltd",
        "complete_address": "1, Bishop Lefroy Road, Kolkata, West Bengal 700020",
        "net_quantity": "500 g",
        "mrp": "₹320",
        "mfg_date": "08/2026",
        "customer_care": "care@tataconsumer.com",
        "country_of_origin": "India",
        "product_category": "domestic",
    }
    return engine.validate(data)


def test_assistant_why_did_this_product_fail(non_compliant_report):
    """Verify assistant explains the exact reasons for non-compliance."""
    assistant = AIComplianceAssistant(non_compliant_report)
    res = assistant.ask("Why did this product fail?")

    assert res["intent"] == "why_failed"
    assert "NON_COMPLIANT" in res["answer"] or "violation" in res["answer"].lower()
    assert len(res["key_findings"]) >= 1
    assert "LM005" in res["relevant_rules"]  # MRP is missing


def test_assistant_which_rules_were_violated(non_compliant_report):
    """Verify assistant lists the violated and warning rules."""
    res = ask_compliance_assistant(non_compliant_report, "Which rules were violated?")

    assert res["intent"] == "violated_rules"
    assert "LM005" in res["relevant_rules"]
    assert any("LM005" in f for f in res["key_findings"])


def test_assistant_how_can_i_fix_the_violations(non_compliant_report):
    """Verify assistant provides step-by-step prioritized corrective actions."""
    res = ask_compliance_assistant(non_compliant_report, "How can I fix the violations?")

    assert res["intent"] == "how_to_fix"
    assert len(res["action_items"]) >= 1
    # Check that recommendation mentions MRP
    actions_text = " ".join(item.get("action", "") for item in res["action_items"])
    assert "MRP" in actions_text


def test_assistant_which_declaration_is_missing(non_compliant_report):
    """Verify assistant identifies missing mandatory declarations."""
    res = ask_compliance_assistant(non_compliant_report, "Which declaration is missing?")

    assert res["intent"] == "missing_declarations"
    assert "LM005" in res["relevant_rules"]
    assert any("Maximum Retail Price" in f or "MRP" in f for f in res["key_findings"])


def test_assistant_what_is_the_highest_priority_issue(non_compliant_report):
    """Verify assistant identifies top priority issue requiring immediate remediation."""
    res = ask_compliance_assistant(non_compliant_report, "What is the highest priority issue?")

    assert res["intent"] == "highest_priority_issue"
    assert len(res["action_items"]) == 1
    assert res["action_items"][0]["priority"] == "Immediate"
    assert res["action_items"][0]["rule_id"] == "LM005"


def test_assistant_compliant_product(compliant_report):
    """Verify assistant correctly responds to compliant reports without reporting false violations."""
    assistant = AIComplianceAssistant(compliant_report)

    res_why = assistant.ask("Why did this product fail?")
    assert "COMPLIANT" in res_why["answer"]
    assert len(res_why["relevant_rules"]) == 0

    res_fix = assistant.ask("How to fix violations?")
    assert "No corrective actions" in res_fix["answer"] or "No remediation required" in res_fix["key_findings"][0]

    summary = generate_compliance_summary(compliant_report)
    assert summary["compliance_score"] == 100.0
    assert summary["overall_status"] == "COMPLIANT"
