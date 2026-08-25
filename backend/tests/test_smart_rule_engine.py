"""Unit tests for the Smart Rule Engine."""
import pytest
from compliance.smart_rule_engine import (
    SmartRuleEngine,
    get_smart_rule_engine,
    validate_smart_compliance,
)
from compliance.status import ValidationStatus


def test_smart_rule_engine_initialization_and_metadata():
    """Verify SmartRuleEngine loads rules with metadata: versions, categories, priorities, effective dates."""
    engine = get_smart_rule_engine()
    assert len(engine.rules) >= 8

    # Verify every rule contains smart metadata
    for rule in engine.rules:
        assert "version" in rule
        assert "priority" in rule
        assert "weight" in rule
        assert "category" in rule
        assert "applicable_to" in rule
        assert "effective_date" in rule
        assert "dependencies" in rule


def test_rule_priority_ordering():
    """Verify rules are prioritized so High priority rules are executed before Medium priority."""
    engine = get_smart_rule_engine()
    priorities = [r.get("priority", "Medium") for r in engine.rules]

    # High priority rules should appear before Medium priority rules
    first_medium_idx = next(i for i, p in enumerate(priorities) if p == "Medium")
    last_high_idx = max(i for i, p in enumerate(priorities) if p == "High")
    assert last_high_idx < first_medium_idx


def test_execution_telemetry_logs():
    """Verify execution logs contain rule_id, rule_name, status, execution_time_ms, category, and priority."""
    sample_product = {
        "product_name": "Organic Honey",
        "manufacturer_name": "Bee Naturals Ltd",
        "complete_address": "Shimla, Himachal Pradesh 171001",
        "net_quantity": "500 g",
        "mrp": "₹350",
        "mfg_date": "07/2026",
        "customer_care": "care@beenaturals.in",
        "country_of_origin": "India",
        "product_category": "domestic",
    }

    report = validate_smart_compliance(sample_product)

    assert "execution_logs" in report
    assert "total_execution_time_ms" in report
    assert report["total_execution_time_ms"] >= 0.0
    assert len(report["execution_logs"]) == len(report["results"])

    first_log = report["execution_logs"][0]
    assert "rule_id" in first_log
    assert "rule_name" in first_log
    assert "category" in first_log
    assert "priority" in first_log
    assert "status" in first_log
    assert "execution_time_ms" in first_log
    assert first_log["execution_time_ms"] >= 0.0


def test_dependency_evaluation():
    """Verify importer details dependency is evaluated only when product is imported."""
    engine = get_smart_rule_engine()

    # Domestic product
    domestic = {"product_name": "Tea", "product_category": "domestic"}
    rep_dom = engine.validate(domestic)
    dom_logs = {log["rule_id"]: log["status"] for log in rep_dom["execution_logs"]}
    assert dom_logs["LM008"] == ValidationStatus.NOT_APPLICABLE.value
    assert dom_logs["LM009"] == ValidationStatus.NOT_APPLICABLE.value

    # Imported product
    imported = {
        "product_name": "Tea",
        "product_category": "imported",
        "country_of_origin": "Sri Lanka",
        "importer_details": "Ceylon Tea Importers, Chennai 600001",
    }
    rep_imp = engine.validate(imported)
    imp_logs = {log["rule_id"]: log["status"] for log in rep_imp["execution_logs"]}
    assert imp_logs["LM008"] == ValidationStatus.PASS.value
    assert imp_logs["LM009"] == ValidationStatus.PASS.value


def test_future_rule_addition_without_code_changes():
    """Verify dynamically injected rules in JSON format execute automatically without code modifications."""
    custom_rules = [
        {
            "rule_id": "SMART_FSSAI_001",
            "version": "1.0.0",
            "rule_name": "FSSAI License Number",
            "category": "Safety",
            "priority": "High",
            "weight": 20,
            "field": "fssai_license",
            "mandatory": True,
            "applicable_to": "food",
            "effective_date": "2020-01-01",
            "dependencies": [{"type": "scope", "requires": "food"}],
            "validation_type": "required",
            "severity": "High",
            "description": "14-digit FSSAI license number must be declared on food packages.",
            "failure_message": "FSSAI license number is missing.",
            "recommendation": "Display 14-digit FSSAI license number.",
            "rule_reference": "FSSAI Packaging Regulations, 2018",
        }
    ]

    custom_engine = SmartRuleEngine(rules_data=custom_rules)

    # 1. Food product with license
    rep_food = custom_engine.validate({"fssai_license": "10014011002233", "product_category": "food"})
    assert rep_food["results"][0]["status"] == ValidationStatus.PASS.value
    assert rep_food["execution_logs"][0]["category"] == "Safety"

    # 2. Electronics product -> rule is NOT_APPLICABLE
    rep_elec = custom_engine.validate({"product_category": "electronics"})
    assert rep_elec["results"][0]["status"] == ValidationStatus.NOT_APPLICABLE.value
