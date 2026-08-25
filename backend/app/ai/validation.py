"""AI-vs-deterministic compliance validation comparison layer."""
import logging
import uuid
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.enums import ComplianceStatus
from app.models.extracted_field import ExtractedField
from app.models.verification import Verification
from app.services.ai_service import AIService
from app.services.compliance_rules import ALL_RULES

logger = logging.getLogger(__name__)


def validate_ai_vs_deterministic(db: Session, verification_id: uuid.UUID) -> Dict[str, Any]:
    """Perform check-and-balance comparison between deterministic and AI compliance rule outcomes."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise ValueError(f"Verification with ID '{verification_id}' not found.")

    # Load extracted fields
    extracted_fields_stmt = select(ExtractedField).where(ExtractedField.verification_id == verification_id)
    extracted_fields = list(db.scalars(extracted_fields_stmt).all())
    field_map = {f.field_name: f.field_value for f in extracted_fields}

    # 1. Deterministic status evaluation (authoritative)
    det_results = [rule.evaluate(field_map) for rule in ALL_RULES]
    det_failed = sum(1 for r in det_results if r.status == ComplianceStatus.FAIL)
    det_warnings = sum(1 for r in det_results if r.status == ComplianceStatus.WARNING)
    
    det_status_mapped = "NON_COMPLIANT" if (det_failed > 0 or det_warnings > 0) else "COMPLIANT"

    # 2. AI status evaluation (advisory)
    ai_status_mapped = det_status_mapped  # Default to deterministic status as fallback

    settings = get_settings()
    if settings.AI_ENABLED:
        try:
            ai_evaluations = AIService().evaluate_compliance(field_map, ALL_RULES)
            ai_failed = sum(1 for item in ai_evaluations if str(item.get("status", "")).upper() in ["FAIL", "WARNING"])
            ai_status_mapped = "NON_COMPLIANT" if ai_failed > 0 else "COMPLIANT"
        except Exception as e:
            logger.warning(
                f"AI compliance evaluation failed during comparison for verification '{verification_id}', falling back: {e}",
                exc_info=True
            )
            ai_status_mapped = det_status_mapped

    # Compare results
    agreement = (det_status_mapped == ai_status_mapped)
    final_result = det_status_mapped  # DETERMINISTIC MUST WIN ALWAYS
    review_required = not agreement

    if agreement:
        decision_source = "Consensus"
    else:
        decision_source = "Deterministic Engine (Authoritative)"

    return {
        "deterministic_result": det_status_mapped,
        "ai_result": ai_status_mapped,
        "agreement": agreement,
        "final_result": final_result,
        "review_required": review_required,
        "decision_source": decision_source,
    }
