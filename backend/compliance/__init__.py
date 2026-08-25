"""Compliance package for Legal Metrology verification."""
from compliance.ai_assistant import (
    AIComplianceAssistant,
    AssistantResponse,
    ask_compliance_assistant,
    generate_compliance_summary,
)
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
from compliance.smart_rule_engine import (
    RuleExecutionLog,
    SmartRuleEngine,
    get_smart_rule_engine,
    validate_smart_compliance,
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
    "AIComplianceAssistant",
    "AssistantResponse",
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
    "RuleExecutionLog",
    "ScoreBreakdownItem",
    "SmartRuleEngine",
    "StatusEvaluator",
    "ValidationStatus",
    "ViolationExplanation",
    "ViolationExplanationEngine",
    "ask_compliance_assistant",
    "calculate_compliance_score",
    "generate_compliance_summary",
    "generate_corrective_recommendations",
    "generate_violation_explanations",
    "get_compliance_engine",
    "get_compliance_scorer",
    "get_explanation_engine",
    "get_recommendation_engine",
    "get_smart_rule_engine",
    "validate_smart_compliance",
    "verify_compliance",
]
