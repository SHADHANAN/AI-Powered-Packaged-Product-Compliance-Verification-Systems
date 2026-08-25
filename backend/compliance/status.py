"""Status evaluation module for the Legal Metrology Compliance Rule Engine.

Provides an intelligent four-state validation model (PASS, WARNING, FAIL, NOT_APPLICABLE)
and overall compliance aggregation with support for OCR confidence scoring and manual review triggers.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_THRESHOLD = 0.70


class ValidationStatus(str, Enum):
    """The four-state validation model for individual compliance rules."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# Alias for compatibility
ComplianceStatus = ValidationStatus


class OverallStatus(str, Enum):
    """Overall compliance status for the packaged commodity verification report."""

    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"


OverallComplianceStatus = OverallStatus


@dataclass
class RuleEvaluationResult:
    """Structured result of a single compliance rule evaluation."""

    rule_id: str
    rule_name: str
    status: ValidationStatus
    message: str
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    field: Optional[str] = None
    actual_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary matching compliance schema."""
        res: Dict[str, Any] = {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status.value,
            "message": self.message,
            "recommendation": self.recommendation,
        }
        return res


class StatusEvaluator:
    """Intelligent status evaluator for compliance rules.

    Evaluates whether a field validation qualifies as PASS, WARNING, FAIL, or NOT_APPLICABLE,
    factoring in validation outcomes, OCR confidence levels, readability indicators,
    and manual verification recommendations.
    """

    def __init__(
        self,
        default_confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        """Initialize StatusEvaluator.

        Args:
            default_confidence_threshold: Default OCR confidence score threshold (0.0 - 1.0).
        """
        self.default_confidence_threshold = default_confidence_threshold
        self._custom_evaluators: List[
            Callable[[ValidationStatus, Any, Optional[float], Dict[str, Any], Dict[str, Any]], Optional[Tuple[ValidationStatus, str, Optional[str]]]]
        ] = []

    def register_custom_evaluator(
        self,
        evaluator_func: Callable[[ValidationStatus, Any, Optional[float], Dict[str, Any], Dict[str, Any]], Optional[Tuple[ValidationStatus, str, Optional[str]]]],
    ) -> None:
        """Register custom status evaluation hook."""
        self._custom_evaluators.append(evaluator_func)

    def evaluate_status(
        self,
        base_status: ValidationStatus,
        base_message: str,
        base_recommendation: Optional[str],
        field_value: Any,
        confidence: Optional[float],
        rule: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ValidationStatus, str, Optional[str]]:
        """Intelligently determine final rule status based on base validation and context.

        Args:
            base_status: Status returned by validator (PASS/WARNING/FAIL/NOT_APPLICABLE).
            base_message: Diagnostic message from validator.
            base_recommendation: Recommended corrective action.
            field_value: Extracted text or value.
            confidence: OCR extraction confidence (0.0 - 1.0).
            rule: Rule configuration dictionary.
            context: Execution context containing thresholds or flags.

        Returns:
            Tuple of (Final ValidationStatus, Final Message, Final Recommendation).
        """
        ctx = context or {}
        threshold = ctx.get("confidence_threshold", self.default_confidence_threshold)

        # 1. NOT_APPLICABLE and FAIL remain as is (failures take precedence over confidence)
        if base_status in {ValidationStatus.NOT_APPLICABLE, ValidationStatus.FAIL}:
            return base_status, base_message, base_recommendation

        # 2. Run custom evaluators if any
        for custom_eval in self._custom_evaluators:
            res = custom_eval(base_status, field_value, confidence, rule, ctx)
            if res is not None:
                return res

        # 3. Check OCR confidence threshold on otherwise PASSING fields
        if confidence is not None and confidence < threshold:
            warning_msg = (
                f"{rule.get('rule_name', 'Field')} was detected as '{field_value}', but OCR confidence "
                f"({confidence:.2f}) is below the required threshold ({threshold:.2f}). Manual verification is recommended."
            )
            warning_rec = (
                rule.get("recommendation")
                or "Verify the packaging label manually to confirm the extracted text accuracy."
            )
            return ValidationStatus.WARNING, warning_msg, warning_rec

        # 4. Check for low-readability indicators in extracted text
        if isinstance(field_value, str) and field_value.strip():
            val_clean = field_value.strip()
            # If text contains high proportion of unreadable/scrambled OCR artifacts
            unreadable_chars = sum(1 for c in val_clean if c in "~`^|§±¿?")
            if unreadable_chars >= 2 or (len(val_clean) > 3 and unreadable_chars / len(val_clean) > 0.2):
                return (
                    ValidationStatus.WARNING,
                    f"Extracted declaration '{val_clean}' contains unreadable OCR artifacts. Manual verification recommended.",
                    rule.get("recommendation") or "Inspect physical package label to verify text clarity.",
                )

        return base_status, base_message, base_recommendation

    @staticmethod
    def calculate_overall_status(
        passed: int,
        failed: int,
        warnings: int,
        not_applicable: int,
    ) -> OverallStatus:
        """Calculate overall compliance status based on aggregated counts.

        Rules:
        - NON_COMPLIANT: At least one mandatory rule failed.
        - PARTIALLY_COMPLIANT: No failures, but one or more warnings (e.g. low confidence or non-standard format).
        - COMPLIANT: All applicable rules passed with high confidence.

        Args:
            passed: Count of passed rules.
            failed: Count of failed rules.
            warnings: Count of warning rules.
            not_applicable: Count of not applicable rules.

        Returns:
            OverallStatus Enum instance.
        """
        if failed > 0:
            return OverallStatus.NON_COMPLIANT
        if warnings > 0:
            return OverallStatus.PARTIALLY_COMPLIANT
        return OverallStatus.COMPLIANT
