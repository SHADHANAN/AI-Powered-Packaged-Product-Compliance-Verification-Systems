"""Tests for compliance.rules configuration and loading."""
import pytest
from compliance.rules import load_legal_metrology_rules, get_rules_list

REQUIRED_FIELDS = [
    "rule_id",
    "rule_name",
    "field",
    "mandatory",
    "applicable_to",
    "validation_type",
    "severity",
    "description",
    "failure_message",
    "recommendation",
    "rule_reference",
]

VALID_APPLICABLE_TO = {"all", "imported", "domestic", "food", "beverage", "cosmetic", "electronics", "medicine"}
VALID_VALIDATION_TYPES = {"required", "date", "currency", "quantity", "address", "contact"}
VALID_SEVERITIES = {"High", "Medium", "Low"}


def test_load_legal_metrology_rules():
    """Verify that the JSON configuration loads and has the expected top-level schema."""
    data = load_legal_metrology_rules()
    assert isinstance(data, dict)
    assert "rules" in data
    assert len(data["rules"]) >= 8


def test_get_rules_list():
    """Verify that get_rules_list returns a list of rule dictionaries."""
    rules = get_rules_list()
    assert isinstance(rules, list)
    assert len(rules) >= 8


def test_rule_fields_and_integrity():
    """Verify that every rule contains all mandatory fields and valid enum values."""
    rules = get_rules_list()
    seen_ids = set()

    for rule in rules:
        # Check all required fields are present
        for field in REQUIRED_FIELDS:
            assert field in rule, f"Rule {rule.get('rule_id')} missing field: {field}"
            assert rule[field] is not None, f"Rule {rule.get('rule_id')} field '{field}' cannot be None"

        rule_id = rule["rule_id"]
        assert rule_id.startswith("LM"), f"Rule ID '{rule_id}' should start with 'LM'"
        assert rule_id not in seen_ids, f"Duplicate rule_id detected: {rule_id}"
        seen_ids.add(rule_id)

        assert isinstance(rule["mandatory"], bool), f"Rule {rule_id} 'mandatory' must be boolean"
        
        applicable_to = rule["applicable_to"]
        if isinstance(applicable_to, list):
            for cat in applicable_to:
                assert cat in VALID_APPLICABLE_TO, f"Invalid applicable_to category '{cat}' in {rule_id}"
        else:
            assert applicable_to in VALID_APPLICABLE_TO, f"Invalid applicable_to in {rule_id}: {applicable_to}"

        assert rule["validation_type"] in VALID_VALIDATION_TYPES, f"Invalid validation_type in {rule_id}: {rule['validation_type']}"
        assert rule["severity"] in VALID_SEVERITIES, f"Invalid severity in {rule_id}: {rule['severity']}"
        assert len(rule["description"].strip()) > 0, f"Empty description in {rule_id}"
        assert len(rule["failure_message"].strip()) > 0, f"Empty failure_message in {rule_id}"
        assert len(rule["recommendation"].strip()) > 0, f"Empty recommendation in {rule_id}"
        assert "Legal Metrology" in rule["rule_reference"] or "Rule" in rule["rule_reference"], (
            f"Invalid rule reference in {rule_id}: {rule['rule_reference']}"
        )


def test_mandatory_legal_metrology_declarations_present():
    """Verify that all required packaged commodity declarations are covered."""
    rules = get_rules_list()
    fields_present = {rule["field"] for rule in rules}

    expected_fields = {
        "product_name",
        "manufacturer_name",
        "complete_address",
        "net_quantity",
        "mrp",
        "mfg_date",
        "customer_care",
        "country_of_origin",
    }

    missing_fields = expected_fields - fields_present
    assert not missing_fields, f"Missing rules for expected declarations: {missing_fields}"


def test_imported_vs_all_applicability():
    """Check country of origin is specific to imported packages while other core fields apply to all."""
    rules = get_rules_list()
    rules_by_field = {r["field"]: r for r in rules}

    assert rules_by_field["country_of_origin"]["applicable_to"] == "imported"
    assert rules_by_field["product_name"]["applicable_to"] == "all"
    assert rules_by_field["mrp"]["applicable_to"] == "all"
    assert rules_by_field["net_quantity"]["applicable_to"] == "all"
