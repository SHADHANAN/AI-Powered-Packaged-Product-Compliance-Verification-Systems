"""Security utilities for AI prompt injection protection."""
import logging
import re
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.enums import AuditAction
from app.services import audit_service

logger = logging.getLogger(__name__)

# List of common prompt injection patterns and instruction override phrases
INJECTION_KEYWORDS = [
    r"ignore previous instructions",
    r"system override",
    r"bypass rules",
    r"mark this product compliant",
    r"ignore instructions",
    r"you are now",
    r"instead of checking",
    r"overwrite",
    r"delete all",
    r"do not evaluate",
    r"override compliance",
    r"rule override",
    r"ignore all instructions",
    r"forget what we talked about",
    r"ignore all previous",
    r"disregard previous",
    r"new instructions",
    r"do not perform",
    r"ignore the rules",
]

# Compile patterns for efficiency (case-insensitive)
INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_KEYWORDS]


class PromptInjectionException(Exception):
    """Exception raised when potential prompt injection is detected in untrusted inputs."""
    pass


def is_prompt_injection(text: str) -> bool:
    """Analyze input text for instruction override signatures or pattern matches."""
    if not text:
        return False
    
    # Check each pattern
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True
            
    # Check for suspicious formatting (e.g. system role emulation)
    system_role_indicators = [
        "system:",
        "instruction:",
        "assistant:",
        "user:",
        "new rule:",
    ]
    text_lower = text.lower()
    for indicator in system_role_indicators:
        if indicator in text_lower:
            if re.search(r"(?:^|\n)\s*" + re.escape(indicator), text_lower):
                return True
                
    return False


def validate_untrusted_text(text: str, context: Optional[str] = None) -> None:
    """Check text for prompt injection. Raise PromptInjectionException if detected."""
    if is_prompt_injection(text):
        # Do not log the sensitive untrusted input itself
        logger.warning(
            f"Security Alert: Potential prompt injection detected in untrusted inputs. "
            f"Context: {context or 'unknown'}."
        )
        raise PromptInjectionException(
            "Security validation failed: suspicious instruction-like patterns detected in input data."
        )


def record_security_event(db: Session, verification_id: Any, details: str) -> None:
    """Record a safe security event in the audit trail without exposing secrets or sensitive data."""
    try:
        from app.models.verification import Verification
        verification = db.get(Verification, verification_id)
        inspector_id = verification.inspector_id if verification else None
        
        # Check if SECURITY_ALERT is in AuditAction, else fallback to COMPLIANCE_CHECKED
        action = AuditAction.COMPLIANCE_CHECKED
        if hasattr(AuditAction, "SECURITY_ALERT"):
            action = AuditAction.SECURITY_ALERT
            
        audit_service.create_audit_log(
            db=db,
            verification_id=verification_id,
            user_id=inspector_id,
            action=action,
            status="FAILED",
            details=f"Security Alert: {details}"
        )
    except Exception as e:
        logger.error(f"Failed to record security event in audit trail: {e}")
