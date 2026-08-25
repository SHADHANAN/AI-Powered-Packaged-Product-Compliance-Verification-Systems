"""Unit tests for category-specific rule validation in the Compliance Rule Engine."""
import pytest
from compliance.engine import ComplianceEngine, get_compliance_engine, verify_compliance
from compliance.status import ValidationStatus


def test_imported_product_category_validation():
    """Verify imported products require Country of Origin and Importer Details."""
    engine = get_compliance_engine()

    # Valid imported product
    valid_imported = {
        "product_name": "Premium Swiss Dark Chocolate",
        "manufacturer_name": "Choc Suisse SA",
        "complete_address": "Zurich, Switzerland",
        "net_quantity": "100 g",
        "mrp": "₹450",
        "mfg_date": "06/2026",
        "customer_care": "support@chocsuisse.in",
        "country_of_origin": "Switzerland",
        "importer_details": "Global Imports Pvt Ltd, Nariman Point, Mumbai 400021",
        "product_category": "imported",
    }

    report = engine.validate(valid_imported)
    results_by_id = {r["rule_id"]: r for r in report["results"]}

    # Country of Origin (LM008) and Importer Details (LM009) must PASS
    assert results_by_id["LM008"]["status"] == ValidationStatus.PASS.value
    assert results_by_id["LM009"]["status"] == ValidationStatus.PASS.value


def test_domestic_product_skips_imported_rules():
    """Verify domestic products treat imported rules (LM008, LM009) as NOT_APPLICABLE."""
    engine = get_compliance_engine()

    domestic_product = {
        "product_name": "Tata Tea Gold",
        "manufacturer_name": "Tata Consumer Products Ltd",
        "complete_address": "1, Bishop Lefroy Road, Kolkata, West Bengal 700020",
        "net_quantity": "500 g",
        "mrp": "₹320",
        "mfg_date": "08/2026",
        "customer_care": "care@tataconsumer.com",
        "product_category": "domestic",
    }

    report = engine.validate(domestic_product)
    results_by_id = {r["rule_id"]: r for r in report["results"]}

    assert results_by_id["LM008"]["status"] == ValidationStatus.NOT_APPLICABLE.value
    assert results_by_id["LM009"]["status"] == ValidationStatus.NOT_APPLICABLE.value
    # Does not reduce score
    assert report["failed"] == 0


def test_food_category_specific_rules():
    """Verify food products trigger expiry rule (LM010) but skip electronics (LM011)."""
    engine = get_compliance_engine()

    food_product = {
        "product_name": "Organic Almond Butter",
        "manufacturer_name": "Nutty Foods Ltd",
        "complete_address": "Pune, Maharashtra 411001",
        "net_quantity": "350 g",
        "mrp": "₹499",
        "mfg_date": "05/2026",
        "expiry_date": "05/2027",
        "customer_care": "care@nuttyfoods.com",
        "product_category": "food",
    }

    report = engine.validate(food_product)
    results_by_id = {r["rule_id"]: r for r in report["results"]}

    # Expiry date (LM010) should be evaluated (PASS)
    assert results_by_id["LM010"]["status"] == ValidationStatus.PASS.value
    # Electronics rule (LM011) should be NOT_APPLICABLE
    assert results_by_id["LM011"]["status"] == ValidationStatus.NOT_APPLICABLE.value


def test_electronics_category_specific_rules():
    """Verify electronics products trigger model/specs rule (LM011) but skip expiry (LM010)."""
    engine = get_compliance_engine()

    electronics_product = {
        "product_name": "Fast USB-C GaN Charger",
        "manufacturer_name": "VoltPower Tech Ltd",
        "complete_address": "Bengaluru, Karnataka 560001",
        "net_quantity": "1 N",
        "mrp": "₹1,499",
        "mfg_date": "08/2026",
        "technical_specs": "Model: VP-65W, Input: 100-240V ~ 50/60Hz 1.5A, Output: 65W Max",
        "customer_care": "1800-888-999",
        "product_category": "electronics",
    }

    report = engine.validate(electronics_product)
    results_by_id = {r["rule_id"]: r for r in report["results"]}

    # Electronics rule (LM011) should PASS
    assert results_by_id["LM011"]["status"] == ValidationStatus.PASS.value
    # Expiry date rule (LM010) should be NOT_APPLICABLE
    assert results_by_id["LM010"]["status"] == ValidationStatus.NOT_APPLICABLE.value


def test_multi_category_combination():
    """Verify combined categories e.g. imported + food triggers both sets of rules."""
    engine = get_compliance_engine()

    imported_food = {
        "product_name": "Italian Extra Virgin Olive Oil",
        "manufacturer_name": "Frantoio Oleario SpA",
        "complete_address": "Lucca, Italy",
        "net_quantity": "1 L",
        "mrp": "₹1,850",
        "mfg_date": "03/2026",
        "expiry_date": "03/2028",
        "customer_care": "oilcare@importer.in",
        "country_of_origin": "Italy",
        "importer_details": "Euro Gourmet Imports LLP, Mumbai 400001",
        "product_category": ["imported", "food"],
    }

    report = engine.validate(imported_food)
    results_by_id = {r["rule_id"]: r for r in report["results"]}

    # Both imported rules (LM008, LM009) and food rule (LM010) must be evaluated
    assert results_by_id["LM008"]["status"] == ValidationStatus.PASS.value
    assert results_by_id["LM009"]["status"] == ValidationStatus.PASS.value
    assert results_by_id["LM010"]["status"] == ValidationStatus.PASS.value
    # Electronics rule remains NOT_APPLICABLE
    assert results_by_id["LM011"]["status"] == ValidationStatus.NOT_APPLICABLE.value


def test_future_category_rule_extensibility():
    """Verify custom future category rules work automatically without modifying engine code."""
    custom_rules = [
        {
            "rule_id": "CUSTOM_TOY_01",
            "rule_name": "Age Appropriateness Warning",
            "field": "age_warning",
            "mandatory": True,
            "applicable_to": "toys",
            "validation_type": "required",
            "severity": "High",
            "weight": 15,
            "description": "Toy packages must declare minimum age suitability (e.g., Not suitable for children under 3 years).",
            "failure_message": "Age suitability warning is missing.",
            "recommendation": "Declare age warning prominently.",
            "rule_reference": "BIS Toy Safety Standards",
        }
    ]

    custom_engine = ComplianceEngine(rules_data=custom_rules)

    # 1. Product in category 'toys' -> rule applied
    toy_data = {"age_warning": "Not suitable for children under 3 years", "product_category": "toys"}
    rep_toy = custom_engine.validate(toy_data)
    assert rep_toy["results"][0]["status"] == ValidationStatus.PASS.value

    # 2. Product in category 'clothing' -> rule NOT_APPLICABLE
    clothing_data = {"product_category": "clothing"}
    rep_clothing = custom_engine.validate(clothing_data)
    assert rep_clothing["results"][0]["status"] == ValidationStatus.NOT_APPLICABLE.value
