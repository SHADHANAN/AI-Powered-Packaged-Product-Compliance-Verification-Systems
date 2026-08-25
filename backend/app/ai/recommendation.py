"""AI-assisted compliance corrective recommendations service module."""
import logging
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.enums import ComplianceStatus
from app.models.compliance_check import ComplianceCheck
from app.services.ai_service import AIService
from app.ai.prompt import format_corrective_recommendation_prompt

logger = logging.getLogger(__name__)


def generate_ai_corrective_recommendations(db: Session, verification_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Generate AI-assisted compliance corrective recommendations based on deterministic violations."""
    # Retrieve failed/warning compliance checks
    stmt = select(ComplianceCheck).where(
        ComplianceCheck.verification_id == verification_id,
        ComplianceCheck.status.in_([ComplianceStatus.FAIL, ComplianceStatus.WARNING]),
    )
    checks = list(db.scalars(stmt).all())

    fallback_recs = _get_fallback_recommendations(checks)

    if not checks:
        return []

    settings = get_settings()
    if settings.AI_ENABLED:
        try:
            from app.ai.security import validate_untrusted_text, record_security_event, PromptInjectionException
            for c in checks:
                if c.message:
                    validate_untrusted_text(c.message, context=f"Violation message '{c.rule_code}' in recommendations")
                if c.actual_value:
                    validate_untrusted_text(c.actual_value, context=f"Violation actual value '{c.rule_code}' in recommendations")

            # Build list of violation inputs for prompt
            violations_data = []
            for c in checks:
                violations_data.append({
                    "rule_code": c.rule_code,
                    "rule_name": c.rule_name,
                    "message": c.message,
                    "expected_value": c.expected_value or "N/A",
                    "actual_value": c.actual_value or "N/A",
                })

            prompt_text = format_corrective_recommendation_prompt(violations_data)

            # Generate AI text response
            ai_service = AIService()
            ai_raw = ai_service.generate_text(prompt_text)

            # Parse JSON list
            ai_parsed = ai_service._parse_json_response(ai_raw)

            # Post-process to enforce advisory limits and verify structure
            processed_recs = []
            for item in ai_parsed:
                issue = item.get("issue", "Compliance non-conformity detected.")
                rec = item.get("recommendation", "Review packaging declarations.")
                evidence = item.get("supporting_evidence", "Regulatory standards context.")
                confidence = float(item.get("confidence", 0.8))

                # Append advisory suffix if not explicitly present
                if "advisory" not in rec.lower():
                    rec += " (Advisory recommendation only)"

                processed_recs.append({
                    "issue": issue,
                    "recommendation": rec,
                    "supporting_evidence": evidence,
                    "confidence": confidence,
                })
            return processed_recs
        except Exception as e:
            logger.warning(f"AI corrective recommendation generation failed, falling back: {e}", exc_info=True)
            if isinstance(e, PromptInjectionException):
                record_security_event(db, verification_id, details="Prompt injection attempt blocked during recommendation generation.")
            return fallback_recs
    else:
        return fallback_recs


def _get_fallback_recommendations(checks: List[ComplianceCheck]) -> List[Dict[str, Any]]:
    """Compose safe deterministic fallback recommendations."""
    recs = []
    for c in checks:
        rec_text = c.recommendation or f"Review packaging label to ensure '{c.rule_name}' meets Legal Metrology standards."
        recs.append({
            "issue": c.message,
            "recommendation": f"{rec_text} (Advisory recommendation only)",
            "supporting_evidence": f"Rule code: {c.rule_code}. Expected format/value: {c.expected_value or 'N/A'}",
            "confidence": 0.9,
        })
    return recs
