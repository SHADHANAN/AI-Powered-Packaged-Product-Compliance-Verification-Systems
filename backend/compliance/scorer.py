"""Compliance Scoring Engine for Packaged Commodity Compliance Verification.

Calculates compliance scores, risk levels, and overall statuses based on
rule evaluation results and configurable Legal Metrology rule weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from compliance.rules import DEFAULT_RULES_PATH, get_rules_list
from compliance.status import OverallStatus, ValidationStatus

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Compliance risk assessment classification levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


DEFAULT_STATUS_MULTIPLIERS: Dict[str, float] = {
    ValidationStatus.PASS.value: 1.0,        # 100% of weight
    ValidationStatus.WARNING.value: 0.5,     # 50% of weight
    ValidationStatus.FAIL.value: 0.0,        # 0% of weight
    ValidationStatus.NOT_APPLICABLE.value: 0.0,  # Excluded from calculation
}

# Default severity weight fallbacks if rule has no explicit weight
SEVERITY_WEIGHT_MAP: Dict[str, float] = {
    "high": 15.0,
    "critical": 20.0,
    "medium": 10.0,
    "low": 5.0,
}
DEFAULT_RULE_WEIGHT = 10.0


@dataclass
class ScoreBreakdownItem:
    """Individual rule scoring breakdown."""

    rule_id: str
    rule_name: Optional[str]
    status: str
    weight: float
    earned_weight: float
    multiplier: float
    is_applicable: bool

    def to_dict(self) -> Dict[str, Any]:
        """Serialize breakdown item to dictionary."""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status,
            "weight": self.weight,
            "earned_weight": self.earned_weight,
            "multiplier": self.multiplier,
            "is_applicable": self.is_applicable,
        }


@dataclass
class ComplianceScoreReport:
    """Consolidated compliance score report."""

    compliance_score: float
    overall_status: OverallStatus
    risk_level: RiskLevel
    total_applicable_weight: float
    earned_weight: float
    passed_count: int
    warning_count: int
    failed_count: int
    not_applicable_count: int
    breakdown: List[ScoreBreakdownItem]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize scoring report to dictionary."""
        return {
            "compliance_score": round(self.compliance_score, 1),
            "overall_status": self.overall_status.value,
            "risk_level": self.risk_level.value,
            "total_applicable_weight": round(self.total_applicable_weight, 2),
            "earned_weight": round(self.earned_weight, 2),
            "passed_count": self.passed_count,
            "warning_count": self.warning_count,
            "failed_count": self.failed_count,
            "not_applicable_count": self.not_applicable_count,
            "breakdown": [item.to_dict() for item in self.breakdown],
        }


class ComplianceScorer:
    """Configurable compliance scoring engine.

    Calculates earned weights, total applicable weights, percentage compliance scores,
    risk levels, and overall compliance statuses from rule evaluation results.
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        status_multipliers: Optional[Dict[str, float]] = None,
        compliant_threshold: float = 90.0,
        warning_threshold: float = 70.0,
    ) -> None:
        """Initialize the Compliance Scorer.

        Args:
            rules_path: Optional path to JSON rules configuration.
            custom_weights: Optional dictionary of rule_id -> custom weight overrides.
            status_multipliers: Optional status weight multipliers map.
            compliant_threshold: Minimum score for COMPLIANT status (default: 90.0).
            warning_threshold: Minimum score for PARTIALLY_COMPLIANT status (default: 70.0).
        """
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self.custom_weights = custom_weights or {}
        self.status_multipliers = status_multipliers or DEFAULT_STATUS_MULTIPLIERS
        self.compliant_threshold = compliant_threshold
        self.warning_threshold = warning_threshold

        self._rule_weights_cache: Dict[str, float] = {}
        self._rule_names_cache: Dict[str, str] = {}
        self._load_rule_metadata()

    def _load_rule_metadata(self) -> None:
        """Extract rule weights and names from JSON configuration."""
        if not self.rules_path.exists():
            logger.warning("Rules configuration file not found at %s. Using default weights.", self.rules_path)
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            rules = data.get("rules", [])
            for r in rules:
                rule_id = r.get("rule_id")
                if not rule_id:
                    continue

                self._rule_names_cache[rule_id] = r.get("rule_name", rule_id)

                # Determine weight from rule config or severity fallback
                if "weight" in r and r["weight"] is not None:
                    try:
                        self._rule_weights_cache[rule_id] = float(r["weight"])
                    except (ValueError, TypeError):
                        self._rule_weights_cache[rule_id] = DEFAULT_RULE_WEIGHT
                else:
                    sev = str(r.get("severity", "medium")).lower()
                    self._rule_weights_cache[rule_id] = SEVERITY_WEIGHT_MAP.get(sev, DEFAULT_RULE_WEIGHT)

        except Exception as exc:
            logger.error("Failed to load rule weights from %s: %s", self.rules_path, exc)

    def get_rule_weight(self, rule_id: str) -> float:
        """Retrieve the configured weight for a given rule_id."""
        if rule_id in self.custom_weights:
            return float(self.custom_weights[rule_id])
        return self._rule_weights_cache.get(rule_id, DEFAULT_RULE_WEIGHT)

    def calculate_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from compliance score.

        Scoring brackets:
        - 90 - 100: LOW
        - 70 - 89.9: MEDIUM
        - Below 70: HIGH
        """
        if score >= self.compliant_threshold:
            return RiskLevel.LOW
        elif score >= self.warning_threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def calculate_overall_status(self, score: float) -> OverallStatus:
        """Determine overall compliance status from compliance score.

        Scoring brackets:
        - Score >= 90: COMPLIANT
        - 70 <= Score < 90: PARTIALLY_COMPLIANT
        - Score < 70: NON_COMPLIANT
        """
        if score >= self.compliant_threshold:
            return OverallStatus.COMPLIANT
        elif score >= self.warning_threshold:
            return OverallStatus.PARTIALLY_COMPLIANT
        else:
            return OverallStatus.NON_COMPLIANT

    def calculate_score(
        self,
        evaluation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Calculate the compliance score and risk evaluation from rule results.

        Args:
            evaluation_input: Dictionary with 'results' key or list of rule evaluation result dicts.

        Returns:
            Structured dictionary containing compliance_score, overall_status, risk_level,
            total_applicable_weight, earned_weight, and rule breakdown.
        """
        if isinstance(evaluation_input, dict):
            raw_results = evaluation_input.get("results", [])
        elif isinstance(evaluation_input, list):
            raw_results = evaluation_input
        else:
            raise ValueError(f"Expected evaluation_input to be a dict or list, got {type(evaluation_input)}")

        total_applicable_weight = 0.0
        earned_weight = 0.0
        passed_count = 0
        warning_count = 0
        failed_count = 0
        not_applicable_count = 0
        breakdown_items: List[ScoreBreakdownItem] = []

        for item in raw_results:
            rule_id = item.get("rule_id", "UNKNOWN")
            rule_name = item.get("rule_name") or self._rule_names_cache.get(rule_id, rule_id)
            status_raw = str(item.get("status", ValidationStatus.FAIL.value)).upper().strip()

            weight = self.get_rule_weight(rule_id)

            if status_raw == ValidationStatus.NOT_APPLICABLE.value:
                not_applicable_count += 1
                breakdown_items.append(
                    ScoreBreakdownItem(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        status=status_raw,
                        weight=weight,
                        earned_weight=0.0,
                        multiplier=0.0,
                        is_applicable=False,
                    )
                )
                continue

            # Applicable rule
            multiplier = self.status_multipliers.get(status_raw, 0.0)
            rule_earned = weight * multiplier

            total_applicable_weight += weight
            earned_weight += rule_earned

            if status_raw == ValidationStatus.PASS.value:
                passed_count += 1
            elif status_raw == ValidationStatus.WARNING.value:
                warning_count += 1
            else:
                failed_count += 1

            breakdown_items.append(
                ScoreBreakdownItem(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    status=status_raw,
                    weight=weight,
                    earned_weight=rule_earned,
                    multiplier=multiplier,
                    is_applicable=True,
                )
            )

        # Calculate final percentage score
        if total_applicable_weight > 0:
            score = (earned_weight / total_applicable_weight) * 100.0
        else:
            score = 100.0

        score = max(0.0, min(100.0, score))

        # Regulatory status determination: any failure forces NON_COMPLIANT
        if failed_count > 0:
            overall_status = OverallStatus.NON_COMPLIANT
            risk_level = RiskLevel.HIGH
        elif warning_count > 0 or score < self.compliant_threshold:
            overall_status = OverallStatus.PARTIALLY_COMPLIANT
            risk_level = RiskLevel.MEDIUM if score >= self.warning_threshold else RiskLevel.HIGH
        else:
            overall_status = OverallStatus.COMPLIANT
            risk_level = RiskLevel.LOW

        report = ComplianceScoreReport(
            compliance_score=score,
            overall_status=overall_status,
            risk_level=risk_level,
            total_applicable_weight=total_applicable_weight,
            earned_weight=earned_weight,
            passed_count=passed_count,
            warning_count=warning_count,
            failed_count=failed_count,
            not_applicable_count=not_applicable_count,
            breakdown=breakdown_items,
        )

        logger.info(
            "Compliance Score calculated: %.1f%% (%s, Risk: %s) [Earned: %.1f/%.1f]",
            score,
            overall_status.value,
            risk_level.value,
            earned_weight,
            total_applicable_weight,
        )

        return report.to_dict()


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_scorer: Optional[ComplianceScorer] = None


def get_compliance_scorer() -> ComplianceScorer:
    """Return a singleton instance of ComplianceScorer."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = ComplianceScorer()
    return _default_scorer


def calculate_compliance_score(
    evaluation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate compliance score, status, and risk level from rule validation results.

    Args:
        evaluation_input: Results dictionary or list from ComplianceEngine.
        custom_weights: Optional custom rule weights dictionary.

    Returns:
        Structured compliance score dictionary.
    """
    if custom_weights:
        scorer = ComplianceScorer(custom_weights=custom_weights)
        return scorer.calculate_score(evaluation_input)

    scorer = get_compliance_scorer()
    return scorer.calculate_score(evaluation_input)
