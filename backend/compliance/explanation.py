"""Violation Explanation Engine for Legal Metrology Compliance Verification.

Generates human-readable, context-aware regulatory explanations for compliance
failures and warnings based on dynamic Legal Metrology rule metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class ViolationExplanation:
    """Detailed structured explanation of a compliance violation or warning."""

    rule_id: str
    rule_name: str
    status: str
    severity: str
    violation: str
    explanation: str
    rule_reference: str
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert explanation to dictionary representation."""
        data: Dict[str, Any] = {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status,
            "severity": self.severity,
            "violation": self.violation,
            "explanation": self.explanation,
            "rule_reference": self.rule_reference,
        }
        if self.recommendation:
            data["recommendation"] = self.recommendation
        return data


class ViolationExplanationEngine:
    """Dynamic regulatory violation explanation generator.

    Loads rule metadata directly from configuration and creates human-readable
    explanations for FAIL and WARNING outcomes without hardcoded text.
    """

    def __init__(
        self,
        rules_path: Optional[Union[str, Path]] = None,
        rules_data: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize the Violation Explanation Engine.

        Args:
            rules_path: Path to Legal Metrology rules JSON configuration.
            rules_data: Optional pre-loaded list of rule definitions.
        """
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self._rules_by_id: Dict[str, Dict[str, Any]] = {}

        if rules_data is not None:
            self._index_rules(rules_data)
        else:
            self._load_and_index_rules()

        logger.info("ViolationExplanationEngine initialized with %d indexed rules.", len(self._rules_by_id))

    def _load_and_index_rules(self) -> None:
        """Load rules from disk and index by rule_id."""
        if not self.rules_path.exists():
            logger.warning("Rules file not found at: %s", self.rules_path)
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._index_rules(data.get("rules", []))
        except Exception as exc:
            logger.error("Failed to load rules for explanation engine from %s: %s", self.rules_path, exc)

    def _index_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Index rules dictionary by rule_id."""
        for r in rules:
            rule_id = r.get("rule_id")
            if rule_id:
                self._rules_by_id[rule_id] = r

    def _generate_violation_title(
        self,
        rule_name: str,
        status: str,
        message: Optional[str],
    ) -> str:
        """Derive a concise violation title dynamically from rule and outcome."""
        msg_lower = (message or "").lower()

        if status == ValidationStatus.FAIL.value:
            if "missing" in msg_lower or "absent" in msg_lower or "cannot be identified" in msg_lower:
                return f"{rule_name} Missing"
            elif "invalid" in msg_lower or "unparseable" in msg_lower:
                return f"{rule_name} Invalid Format"
            elif "greater than zero" in msg_lower or "positive" in msg_lower:
                return f"{rule_name} Illegal Value"
            return f"{rule_name} Non-Compliance"

        # WARNING status
        if "confidence" in msg_lower:
            return f"{rule_name} Low OCR Confidence"
        elif "artifact" in msg_lower or "unreadable" in msg_lower:
            return f"{rule_name} Unclear Text"
        elif "unit" in msg_lower or "format" in msg_lower:
            return f"{rule_name} Format Discrepancy"

        return f"{rule_name} Warning"

    def _compose_explanation(
        self,
        rule_meta: Dict[str, Any],
        status: str,
        message: Optional[str],
    ) -> str:
        """Compose human-readable regulatory explanation from rule metadata and message."""
        description = rule_meta.get("description", "").strip()
        rule_ref = rule_meta.get("rule_reference", "Legal Metrology (Packaged Commodities) Rules, 2011").strip()
        failure_msg = rule_meta.get("failure_message", "").strip()

        # Clean description ending
        if description and not description.endswith("."):
            description += "."

        if status == ValidationStatus.FAIL.value:
            specific_reason = message or failure_msg or "This mandatory declaration is missing or invalid on the packaging label."
            if not specific_reason.endswith("."):
                specific_reason += "."

            return (
                f"{description} {specific_reason} Under {rule_ref}, pre-packaged commodities lacking "
                f"this mandatory declaration are non-compliant and liable for regulatory action."
            )

        # Status == WARNING
        warn_reason = message or "The declaration was detected but may have readability or formatting issues."
        if not warn_reason.endswith("."):
            warn_reason += "."

        return (
            f"{description} {warn_reason} While a declaration was identified, manual inspection is recommended "
            f"to verify compliance with {rule_ref}."
        )

    def explain_rule_violation(self, rule_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate an explanation dictionary for an individual rule result if FAIL or WARNING.

        Args:
            rule_result: Result dictionary from ComplianceEngine containing rule_id, status, message, etc.

        Returns:
            ViolationExplanation dictionary if status is FAIL or WARNING, otherwise None.
        """
        status = str(rule_result.get("status", "")).upper().strip()

        # Only process FAIL and WARNING
        if status in EXCLUDED_STATUSES or not status:
            return None

        rule_id = rule_result.get("rule_id", "UNKNOWN")
        rule_meta = self._rules_by_id.get(rule_id, {})

        rule_name = (
            rule_result.get("rule_name")
            or rule_meta.get("rule_name")
            or rule_id
        )
        severity = rule_meta.get("severity", "Medium")
        rule_ref = rule_meta.get("rule_reference", "Legal Metrology (Packaged Commodities) Rules, 2011")
        recommendation = rule_result.get("recommendation") or rule_meta.get("recommendation")
        message = rule_result.get("message")

        violation_title = self._generate_violation_title(rule_name, status, message)
        explanation_text = self._compose_explanation(rule_meta, status, message)

        item = ViolationExplanation(
            rule_id=rule_id,
            rule_name=rule_name,
            status=status,
            severity=severity,
            violation=violation_title,
            explanation=explanation_text,
            rule_reference=rule_ref,
            recommendation=recommendation,
        )
        return item.to_dict()

    def generate_explanations(
        self,
        validation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Generate structured explanations for all failures and warnings in validation results.

        Args:
            validation_input: Results dictionary from ComplianceEngine (e.g. {'results': [...]})
                             or list of result dicts.

        Returns:
            List of violation explanation dictionaries.
        """
        if isinstance(validation_input, dict):
            results = validation_input.get("results", [])
        elif isinstance(validation_input, list):
            results = validation_input
        else:
            raise ValueError(f"Expected validation_input to be dict or list, got {type(validation_input)}")

        explanations: List[Dict[str, Any]] = []

        for res in results:
            explained = self.explain_rule_violation(res)
            if explained is not None:
                explanations.append(explained)

        logger.info("Generated %d violation explanations.", len(explanations))
        return explanations


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_explanation_engine: Optional[ViolationExplanationEngine] = None


def get_explanation_engine() -> ViolationExplanationEngine:
    """Return a singleton instance of ViolationExplanationEngine."""
    global _default_explanation_engine
    if _default_explanation_engine is None:
        _default_explanation_engine = ViolationExplanationEngine()
    return _default_explanation_engine


def generate_violation_explanations(
    validation_input: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Generate human-readable regulatory violation explanations for FAIL and WARNING results.

    Args:
        validation_input: Validation report dict or list of rule results.

    Returns:
        List of structured violation explanation dictionaries.
    """
    engine = get_explanation_engine()
    return engine.generate_explanations(validation_input)
