"""Compliance package for Legal Metrology verification."""
from compliance.engine import (
    ComplianceEngine,
    get_compliance_engine,
    verify_compliance,
)
from compliance.explanation import (
    ViolationExplanation,
    ViolationExplanationEngine,
    generate_violation_explanations,
    get_explanation_engine,
)
from compliance.recommendation import (
    CorrectiveRecommendation,
    RecommendationEngine,
    RecommendationPriority,
    generate_corrective_recommendations,
    get_recommendation_engine,
)
from compliance.scorer import (
    ComplianceScoreReport,
    ComplianceScorer,
    RiskLevel,
    ScoreBreakdownItem,
    calculate_compliance_score,
    get_compliance_scorer,
)
from compliance.status import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    ComplianceStatus,
    OverallComplianceStatus,
    OverallStatus,
    RuleEvaluationResult,
    StatusEvaluator,
    ValidationStatus,
)

__all__ = [
    "ComplianceEngine",
    "ComplianceScoreReport",
    "ComplianceScorer",
    "ComplianceStatus",
    "CorrectiveRecommendation",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "OverallComplianceStatus",
    "OverallStatus",
    "RecommendationEngine",
    "RecommendationPriority",
    "RiskLevel",
    "RuleEvaluationResult",
    "ScoreBreakdownItem",
    "StatusEvaluator",
    "ValidationStatus",
    "ViolationExplanation",
    "ViolationExplanationEngine",
    "calculate_compliance_score",
    "generate_corrective_recommendations",
    "generate_violation_explanations",
    "get_compliance_engine",
    "get_compliance_scorer",
    "get_explanation_engine",
    "get_recommendation_engine",
    "verify_compliance",
]
