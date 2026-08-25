"""Corrective Recommendation Engine for Legal Metrology Compliance Verification.

Generates prioritized, actionable corrective guidance for packaging compliance issues
(FAIL and WARNING) identified by the Compliance Rule Engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from compliance.rules import DEFAULT_RULES_PATH
from compliance.status import ValidationStatus

logger = logging.getLogger(__name__)

EXCLUDED_STATUSES = {
    ValidationStatus.PASS.value,
    ValidationStatus.NOT_APPLICABLE.value,
}


class RecommendationPriority(str, Enum):
    """Actionable urgency levels for corrective packaging recommendations."""

    IMMEDIATE = "Immediate"
    RECOMMENDED = "Recommended"
    OPTIONAL = "Optional"


# Severity to Action Priority mapping
SEVERITY_TO_PRIORITY_MAP: Dict[str, RecommendationPriority] = {
    "high": RecommendationPriority.IMMEDIATE,
    "critical": RecommendationPriority.IMMEDIATE,
    "medium": RecommendationPriority.RECOMMENDED,
    "low": RecommendationPriority.OPTIONAL,
}


@dataclass
class CorrectiveRecommendation:
    """Actionable corrective recommendation item."""

    rule_id: str
    rule_name: str
    recommendation: str
    priority: str
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "recommendation": self.recommendation,
            "priority": self.priority,
            "severity": self.severity,
        }


class RecommendationEngine:
    """Dynamic corrective recommendation generator for Legal Metrology compliance.

    Extracts recommended corrective actions dynamically from rule definitions,
    maps regulatory severity to operational priorities, and generates clean
    guidance reports for manufacturers and compliance auditors.
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize the Recommendation Engine.

        Args:
            rules_path: Optional path to JSON rules configuration.
            rules_data: Optional pre-loaded list of rule definitions.
        """
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self._rules_by_id: Dict[str, Dict[str, Any]] = {}

        if rules_data is not None:
            self._index_rules(rules_data)
        else:
            self._load_and_index_rules()

        logger.info("RecommendationEngine initialized with %d indexed rules.", len(self._rules_by_id))

    def _load_and_index_rules(self) -> None:
        """Load rules from disk and index by rule_id."""
        if not self.rules_path.exists():
            logger.warning("Rules configuration file not found at: %s", self.rules_path)
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._index_rules(data.get("rules", []))
        except Exception as exc:
            logger.error("Failed to load rules for recommendation engine from %s: %s", self.rules_path, exc)

    def _index_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Index rules dictionary by rule_id."""
        for r in rules:
            rule_id = r.get("rule_id")
            if rule_id:
                self._rules_by_id[rule_id] = r

    @staticmethod
    def map_severity_to_priority(severity: str) -> RecommendationPriority:
        """Map regulatory rule severity to actionable recommendation priority.

        Mapping:
        - High / Critical -> Immediate
        - Medium          -> Recommended
        - Low             -> Optional
        """
        sev_clean = str(severity).strip().lower()
        return SEVERITY_TO_PRIORITY_MAP.get(sev_clean, RecommendationPriority.RECOMMENDED)

    def generate_rule_recommendation(self, rule_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a corrective recommendation for a single rule result if FAIL or WARNING.

        Args:
            rule_result: Rule outcome dictionary containing rule_id, status, recommendation, etc.

        Returns:
            Corrective recommendation dictionary if status is FAIL/WARNING, otherwise None.
        """
        status = str(rule_result.get("status", "")).upper().strip()

        # Generate recommendations only for FAIL and WARNING
        if status in EXCLUDED_STATUSES or not status:
            return None

        rule_id = rule_result.get("rule_id", "UNKNOWN")
        rule_meta = self._rules_by_id.get(rule_id, {})

        rule_name = (
            rule_result.get("rule_name")
            or rule_meta.get("rule_name")
            or rule_id
        )
        severity = str(rule_meta.get("severity", "Medium")).capitalize()

        # Recommendation text from result or fallback to rule metadata
        rec_text = (
            rule_result.get("recommendation")
            or rule_meta.get("recommendation")
            or f"Review packaging label to ensure '{rule_name}' meets Legal Metrology standards."
        ).strip()

        priority = self.map_severity_to_priority(severity)

        rec = CorrectiveRecommendation(
            rule_id=rule_id,
            rule_name=rule_name,
            recommendation=rec_text,
            priority=priority.value,
            severity=severity,
        )
        return rec.to_dict()

    def generate_recommendations(
        self,
        validation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Generate corrective recommendations for all failed or warning rules.

        Args:
            validation_input: Validation report dict containing 'results' or list of result dicts.

        Returns:
            List of structured corrective recommendation dictionaries.
        """
        if isinstance(validation_input, dict):
            results = validation_input.get("results", [])
        elif isinstance(validation_input, list):
            results = validation_input
        else:
            raise ValueError(f"Expected validation_input to be dict or list, got {type(validation_input)}")

        recommendations: List[Dict[str, Any]] = []

        for res in results:
            rec = self.generate_rule_recommendation(res)
            if rec is not None:
                recommendations.append(rec)

        logger.info("Generated %d corrective recommendations.", len(recommendations))
        return recommendations


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Return a singleton instance of RecommendationEngine."""
    global _default_recommendation_engine
    if _default_recommendation_engine is None:
        _default_recommendation_engine = RecommendationEngine()
    return _default_recommendation_engine


def generate_corrective_recommendations(
    validation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Generate prioritized corrective recommendations for packaging compliance issues.

    Args:
        validation_input: Validation report dictionary or list of rule results.

    Returns:
        List of structured corrective recommendation dictionaries.
    """
    engine = get_recommendation_engine()
    return engine.generate_recommendations(validation_input)
