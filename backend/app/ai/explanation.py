"""AI-assisted compliance explanation service module."""
import logging
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.enums import ComplianceStatus
from app.models.compliance_check import ComplianceCheck
from app.models.extracted_field import ExtractedField
from app.models.verification import Verification
from app.services.ai_service import AIService
from app.ai.prompt import format_compliance_explanation_prompt

logger = logging.getLogger(__name__)


def generate_ai_compliance_explanation(db: Session, verification_id: uuid.UUID) -> Dict[str, Any]:
    """Generate an AI-assisted compliance explanation based on deterministic verification results."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise ValueError(f"Verification with ID '{verification_id}' not found.")

    # Retrieve compliance checks
    checks_stmt = select(ComplianceCheck).where(ComplianceCheck.verification_id == verification_id)
    checks = list(db.scalars(checks_stmt).all())

    # Retrieve extracted fields
    fields_stmt = select(ExtractedField).where(ExtractedField.verification_id == verification_id)
    fields = list(db.scalars(fields_stmt).all())

    # Determine status
    has_fail = any(c.status == ComplianceStatus.FAIL for c in checks)
    has_warn = any(c.status == ComplianceStatus.WARNING for c in checks)

    if has_fail:
        status_str = "NON_COMPLIANT"
    elif has_warn:
        status_str = "PARTIALLY_COMPLIANT"
    else:
        status_str = "COMPLIANT"

    violations = []
    for c in checks:
        if c.status in (ComplianceStatus.FAIL, ComplianceStatus.WARNING):
            violations.append(f"{c.rule_code}: {c.message}")

    score = verification.overall_score or 0.0

    # Build fallback basic explanation
    fallback_explanation = _get_fallback_explanation(status_str, checks)

    settings = get_settings()
    if settings.AI_ENABLED:
        try:
            # Build prompt inputs
            violations_text = ""
            for c in checks:
                if c.status in (ComplianceStatus.FAIL, ComplianceStatus.WARNING):
                    violations_text += f"- Rule {c.rule_code} ({c.rule_name}): Status={c.status.value.upper()}, Message={c.message}, Expected={c.expected_value or 'N/A'}, Actual={c.actual_value or 'N/A'}\n"
            if not violations_text:
                violations_text = "No violations or warnings detected.\n"

            fields_text = ""
            for f in fields:
                fields_text += f"- {f.field_name}: Value={f.field_value or 'N/A'}, Evidence={f.source_text or 'N/A'}\n"
            if not fields_text:
                fields_text = "No fields extracted.\n"

            prompt_text = format_compliance_explanation_prompt(
                compliance_status=status_str,
                overall_score=score,
                violations_list=violations_text,
                fields_list=fields_text,
            )

            # Generate AI text response
            ai_service = AIService()
            ai_explanation = ai_service.generate_text(prompt_text)

            # AI validation constraint: If the deterministic engine says COMPLIANT,
            # AI must not independently declare it NON_COMPLIANT or claim failure.
            ai_explanation_lower = ai_explanation.lower()
            if status_str == "COMPLIANT" and (
                "non-compliant" in ai_explanation_lower
                or "non_compliant" in ai_explanation_lower
                or "fail" in ai_explanation_lower
                or "violation" in ai_explanation_lower
            ):
                logger.warning("AI explanation contradicted COMPLIANT status; falling back to deterministic explanation.")
                explanation_text = fallback_explanation
            else:
                explanation_text = ai_explanation.strip()
        except Exception as e:
            logger.warning(f"AI compliance explanation generation failed, falling back: {e}", exc_info=True)
            explanation_text = fallback_explanation
    else:
        explanation_text = fallback_explanation

    return {
        "verification_id": verification_id,
        "status": status_str,
        "score": score,
        "explanation": explanation_text,
        "violations": violations,
    }


def _get_fallback_explanation(status: str, checks: List[ComplianceCheck]) -> str:
    """Compose basic human-readable fallback explanation."""
    if status == "COMPLIANT":
        return "The product is fully compliant with all evaluated Legal Metrology rules. All mandatory declarations are present and valid."

    failures = [c for c in checks if c.status == ComplianceStatus.FAIL]
    warnings = [c for c in checks if c.status == ComplianceStatus.WARNING]

    explanation_parts = []
    if failures:
        explanation_parts.append(
            "The product is non-compliant due to the following violation(s): "
            + ", ".join(f"{c.rule_name} ({c.message})" for c in failures) + "."
        )
    if warnings:
        explanation_parts.append(
            "The product requires manual verification due to the following warning(s): "
            + ", ".join(f"{c.rule_name} ({c.message})" for c in warnings) + "."
        )

    return " ".join(explanation_parts)
