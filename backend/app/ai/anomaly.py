"""AI-assisted product label anomaly detection service module."""
import json
import logging
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.extracted_field import ExtractedField
from app.models.verification import Verification
from app.services.ai_service import AIService
from app.ai.prompt import format_anomaly_detection_prompt

logger = logging.getLogger(__name__)


def generate_ai_anomaly_detection(db: Session, verification_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Perform AI-assisted product packaging label anomaly detection with fallback."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise ValueError(f"Verification with ID '{verification_id}' not found.")

    # Retrieve extracted fields
    stmt = select(ExtractedField).where(ExtractedField.verification_id == verification_id)
    fields = list(db.scalars(stmt).all())

    fallback_anomalies = _get_fallback_anomalies(fields)

    settings = get_settings()
    if settings.AI_ENABLED:
        try:
            from app.ai.security import validate_untrusted_text, record_security_event, PromptInjectionException
            if verification.ocr_raw_text:
                validate_untrusted_text(verification.ocr_raw_text, context="OCR raw text in anomalies")
            for f in fields:
                if f.field_value:
                    validate_untrusted_text(str(f.field_value), context=f"Field '{f.field_name}' in anomalies")

            # Format extracted fields for prompt
            fields_data = []
            for f in fields:
                fields_data.append({
                    "field_name": f.field_name,
                    "field_value": f.field_value,
                    "confidence": f.confidence,
                    "source_text": f.source_text,
                })

            prompt_text = format_anomaly_detection_prompt(
                raw_text=verification.ocr_raw_text or "",
                fields=fields_data,
            )

            # Generate AI text response
            ai_service = AIService()
            ai_raw = ai_service.generate_text(prompt_text)

            # Parse JSON list
            ai_parsed = ai_service._parse_json_response(ai_raw)

            # Post-process to ensure safety and advisory context
            processed_anomalies = []
            for item in ai_parsed:
                detected = bool(item.get("anomaly_detected", False))
                if not detected:
                    continue

                a_type = item.get("anomaly_type", "Label Anomaly")
                severity = item.get("severity", "MEDIUM").upper()
                evidence = item.get("evidence", "Label text context")
                confidence = float(item.get("confidence", 0.8))
                explanation = item.get("explanation", "Potential anomaly identified.")

                # Ensure advisory framing in the explanation
                if "advisory" not in explanation.lower():
                    explanation += " (Advisory signal only; does not declare legal non-compliance)"

                processed_anomalies.append({
                    "anomaly_detected": detected,
                    "anomaly_type": a_type,
                    "severity": severity,
                    "evidence": evidence,
                    "confidence": confidence,
                    "explanation": explanation,
                })
            return processed_anomalies
        except Exception as e:
            logger.warning(f"AI label anomaly detection failed, falling back: {e}", exc_info=True)
            if isinstance(e, PromptInjectionException):
                record_security_event(db, verification_id, details="Prompt injection attempt blocked during anomaly detection.")
            return fallback_anomalies
    else:
        return fallback_anomalies


def _get_fallback_anomalies(fields: List[ExtractedField]) -> List[Dict[str, Any]]:
    """Compose safe, deterministic fallback anomalies from extracted fields."""
    anomalies = []
    field_names = {f.field_name for f in fields}

    # Check for missing fields
    required = ["mrp", "net_quantity", "manufacturer"]
    for req in required:
        if req not in field_names:
            anomalies.append({
                "anomaly_detected": True,
                "anomaly_type": "Missing Expected Field",
                "severity": "MEDIUM",
                "evidence": f"Field '{req}' not found in label extractions.",
                "confidence": 0.8,
                "explanation": f"The mandatory field '{req}' was not detected. (Advisory signal only; does not declare legal non-compliance)",
            })

    # Check for malformed values
    for f in fields:
        if f.field_name == "mrp" and f.field_value:
            val = f.field_value.lower()
            if not any(char.isdigit() for char in val):
                anomalies.append({
                    "anomaly_detected": True,
                    "anomaly_type": "Malformed Value",
                    "severity": "HIGH",
                    "evidence": f"MRP value: '{f.field_value}'",
                    "confidence": 0.85,
                    "explanation": f"The extracted MRP value '{f.field_value}' does not contain numeric price digits. (Advisory signal only; does not declare legal non-compliance)",
                })

    return anomalies
