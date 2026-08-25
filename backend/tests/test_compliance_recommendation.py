"""Unit tests for compliance.recommendation Corrective Recommendation Engine."""
import pytest
from compliance.recommendation import (
    CorrectiveRecommendation,
    RecommendationEngine,
    RecommendationPriority,
    generate_corrective_recommendations,
    get_recommendation_engine,
)
from compliance.status import ValidationStatus


def test_recommendation_generation_for_failure():
    """Verify recommendation generation for a FAIL rule with High severity."""
    engine = get_recommendation_engine()

    fail_result = {
        "rule_id": "LM005",
        "rule_name": "Maximum Retail Price (MRP)",
        "status": "FAIL",
        "message": "Maximum Retail Price (MRP) declaration is missing.",
        "recommendation": "Declare MRP explicitly in the format 'MRP Rs. / ₹ XX.XX (incl. of all taxes)' on the package in accordance with Rule 6(1)(da).",
    }

    rec = engine.generate_rule_recommendation(fail_result)

    assert rec is not None
    assert rec["rule_id"] == "LM005"
    assert rec["rule_name"] == "Maximum Retail Price (MRP)"
    assert rec["severity"] == "High"
    assert rec["priority"] == RecommendationPriority.IMMEDIATE.value
    assert "MRP" in rec["recommendation"]


def test_priority_mapping_for_severities():
    """Verify priority mapping across High, Medium, and Low severities."""
    assert RecommendationEngine.map_severity_to_priority("High") == RecommendationPriority.IMMEDIATE
    assert RecommendationEngine.map_severity_to_priority("Critical") == RecommendationPriority.IMMEDIATE
    assert RecommendationEngine.map_severity_to_priority("Medium") == RecommendationPriority.RECOMMENDED
    assert RecommendationEngine.map_severity_to_priority("Low") == RecommendationPriority.OPTIONAL


def test_medium_severity_recommendation():
    """Verify Medium severity rule yields Recommended priority."""
    engine = get_recommendation_engine()

    warning_result = {
        "rule_id": "LM006",
        "rule_name": "Month and Year of Manufacture / Packing / Import",
        "status": "WARNING",
        "message": "Date format is non-standard.",
        "recommendation": "Clearly display the date of manufacture or packaging (e.g., 'Mfg Date: 04/2026' or 'Packed: Apr 2026') as mandated under Rule 6(1)(d).",
    }

    rec = engine.generate_rule_recommendation(warning_result)

    assert rec is not None
    assert rec["rule_id"] == "LM006"
    assert rec["severity"] == "Medium"
    assert rec["priority"] == RecommendationPriority.RECOMMENDED.value


def test_pass_and_not_applicable_are_excluded():
    """Verify PASS and NOT_APPLICABLE results produce zero recommendations."""
    engine = get_recommendation_engine()

    pass_result = {"rule_id": "LM001", "status": "PASS", "message": "Product name valid"}
    na_result = {"rule_id": "LM008", "status": "NOT_APPLICABLE", "message": "Not applicable for domestic"}

    assert engine.generate_rule_recommendation(pass_result) is None
    assert engine.generate_rule_recommendation(na_result) is None

    recommendations = engine.generate_recommendations([pass_result, na_result])
    assert len(recommendations) == 0


def test_batch_recommendations_generation():
    """Test generating recommendations for a mixed batch of evaluation outcomes."""
    mixed_results = {
        "results": [
            {"rule_id": "LM001", "status": "PASS"},
            {"rule_id": "LM004", "status": "FAIL", "message": "Net quantity invalid"},
            {"rule_id": "LM007", "status": "FAIL", "message": "Customer care missing"},
            {"rule_id": "LM008", "status": "NOT_APPLICABLE"},
        ]
    }

    recommendations = generate_corrective_recommendations(mixed_results)

    assert len(recommendations) == 2  # Only LM004 and LM007
    rule_ids = {r["rule_id"] for r in recommendations}
    assert rule_ids == {"LM004", "LM007"}
    for rec in recommendations:
        assert rec["priority"] == RecommendationPriority.IMMEDIATE.value


def test_dynamic_future_rule_recommendation():
    """Verify custom/future rules generate recommendations dynamically without code modifications."""
    custom_rules = [
        {
            "rule_id": "CUSTOM_FSSAI",
            "rule_name": "FSSAI Logo & License",
            "severity": "Low",
            "recommendation": "Display the FSSAI logo and 14-digit license number prominently on the label.",
        }
    ]

    custom_engine = RecommendationEngine(rules_data=custom_rules)
    res = custom_engine.generate_rule_recommendation({
        "rule_id": "CUSTOM_FSSAI",
        "status": "FAIL",
    })

    assert res is not None
    assert res["rule_id"] == "CUSTOM_FSSAI"
    assert res["rule_name"] == "FSSAI Logo & License"
    assert res["severity"] == "Low"
    assert res["priority"] == RecommendationPriority.OPTIONAL.value
    assert "FSSAI" in res["recommendation"]
