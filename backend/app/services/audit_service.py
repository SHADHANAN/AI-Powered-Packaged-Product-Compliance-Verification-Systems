import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction
from app.models.verification import Verification
from app.utils.exceptions import NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.services.audit")


def create_audit_log(
    db: Session,
    verification_id: uuid.UUID,
    action: AuditAction,
    user_id: Optional[uuid.UUID] = None,
    status: str = "SUCCESS",
    details: Optional[str] = None,
) -> AuditLog:
    """Record an audit trail event against a verification run."""
    audit_entry = AuditLog(
        verification_id=verification_id,
        user_id=user_id,
        action=action,
        status=status,
        details=details,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    logger.info(f"Audit event '{action.value}' logged for verification '{verification_id}' [status={status}]")
    return audit_entry


def get_verification_audit_logs(db: Session, verification_id: uuid.UUID) -> List[AuditLog]:
    """Retrieve chronological audit trail entries for a verification run."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    stmt = (
        select(AuditLog)
        .where(AuditLog.verification_id == verification_id)
        .order_by(AuditLog.created_at.asc())
    )
    return list(db.scalars(stmt).all())
