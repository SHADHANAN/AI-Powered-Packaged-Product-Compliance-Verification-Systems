"""Unit tests for compliance.scorer Compliance Scoring Engine."""
import pytest
from compliance.scorer import (
    ComplianceScorer,
    RiskLevel,
    calculate_compliance_score,
    get_compliance_scorer,
)
from compliance.status import OverallStatus, ValidationStatus


def test_example_scoring_calculation():
    """Verify score calculation using the prompt's representative test case."""
    example_input = {
        "results": [
            {"rule_id": "LM001", "status": "PASS"},            # weight: 15 -> earned: 15.0
            {"rule_id": "LM002", "status": "FAIL"},            # weight: 15 -> earned: 0.0
            {"rule_id": "LM003", "status": "WARNING"},         # weight: 15 -> earned: 7.5
            {"rule_id": "LM008", "status": "NOT_APPLICABLE"},  # weight: 15 -> excluded
        ]
    }
    # Total applicable weight = 15 + 15 + 15 = 45.0
    # Earned weight = 15.0 + 0.0 + 7.5 = 22.5
    # Score = (22.5 / 45.0) * 100 = 50.0% -> NON_COMPLIANT, HIGH risk

    report = calculate_compliance_score(example_input)

    assert "compliance_score" in report
    assert "overall_status" in report
    assert "risk_level" in report
    assert "total_applicable_weight" in report
    assert "earned_weight" in report

    assert report["total_applicable_weight"] == 45.0
    assert report["earned_weight"] == 22.5
    assert report["compliance_score"] == 50.0
    assert report["overall_status"] == OverallStatus.NON_COMPLIANT.value
    assert report["risk_level"] == RiskLevel.HIGH.value


def test_perfect_compliance_score():
    """Verify 100% score produces COMPLIANT and LOW risk."""
    all_pass = {
        "results": [
            {"rule_id": "LM001", "status": "PASS"},
            {"rule_id": "LM002", "status": "PASS"},
            {"rule_id": "LM003", "status": "PASS"},
            {"rule_id": "LM004", "status": "PASS"},
            {"rule_id": "LM005", "status": "PASS"},
            {"rule_id": "LM006", "status": "PASS"},
            {"rule_id": "LM007", "status": "PASS"},
            {"rule_id": "LM008", "status": "NOT_APPLICABLE"},
        ]
    }
    report = calculate_compliance_score(all_pass)
    assert report["compliance_score"] == 100.0
    assert report["overall_status"] == OverallStatus.COMPLIANT.value
    assert report["risk_level"] == RiskLevel.LOW.value


def test_partially_compliant_and_medium_risk_brackets():
    """Verify score in 70-89 range produces PARTIALLY_COMPLIANT and MEDIUM risk."""
    scorer = get_compliance_scorer()

    # 1 warning out of 7 rules: 6 pass (6 * 15 = 90) + 1 warning (1 * 10 * 0.5 = 5) / (90 + 10 = 100) = 95%
    # Let's craft an 85% scenario:
    # 5 pass (5 * 15 = 75), 2 warnings (2 * 15 * 0.5 = 15) -> 90 / 105 = 85.7%
    custom_results = [
        {"rule_id": "LM001", "status": "PASS"},     # 15
        {"rule_id": "LM002", "status": "PASS"},     # 15
        {"rule_id": "LM003", "status": "PASS"},     # 15
        {"rule_id": "LM004", "status": "PASS"},     # 15
        {"rule_id": "LM005", "status": "PASS"},     # 15
        {"rule_id": "LM006", "status": "WARNING"},  # 10 * 0.5 = 5
        {"rule_id": "LM007", "status": "WARNING"},  # 15 * 0.5 = 7.5
    ]
    # Total = 15*5 + 10 + 15 = 100.0
    # Earned = 75 + 5 + 7.5 = 87.5
    # Score = 87.5% -> PARTIALLY_COMPLIANT, MEDIUM risk
    report = scorer.calculate_score(custom_results)
    assert report["compliance_score"] == 87.5
    assert report["overall_status"] == OverallStatus.PARTIALLY_COMPLIANT.value
    assert report["risk_level"] == RiskLevel.MEDIUM.value


def test_custom_rule_weights_override():
    """Verify custom weights can be supplied dynamically without altering backend code."""
    custom_weights = {
        "CUSTOM_R1": 50.0,
        "CUSTOM_R2": 50.0,
    }
    scorer = ComplianceScorer(custom_weights=custom_weights)

    results = [
        {"rule_id": "CUSTOM_R1", "status": "PASS"},     # 50.0 earned
        {"rule_id": "CUSTOM_R2", "status": "WARNING"},  # 25.0 earned
    ]
    report = scorer.calculate_score(results)
    assert report["total_applicable_weight"] == 100.0
    assert report["earned_weight"] == 75.0
    assert report["compliance_score"] == 75.0
    assert report["overall_status"] == OverallStatus.PARTIALLY_COMPLIANT.value
    assert report["risk_level"] == RiskLevel.MEDIUM.value


def test_empty_or_all_not_applicable_results():
    """Verify safe fallback when all rules are NOT_APPLICABLE or empty."""
    results = [
        {"rule_id": "LM008", "status": "NOT_APPLICABLE"},
    ]
    report = calculate_compliance_score(results)
    assert report["compliance_score"] == 100.0
    assert report["total_applicable_weight"] == 0.0
    assert report["earned_weight"] == 0.0
    assert report["not_applicable_count"] == 1
