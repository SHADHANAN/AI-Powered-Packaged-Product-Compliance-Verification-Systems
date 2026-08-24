import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.schemas.compliance_check import ComplianceCheckCreate
from app.utils.exceptions import NotFoundException


def create_compliance_check(db: Session, check_in: ComplianceCheckCreate) -> ComplianceCheck:
    """Create and persist a compliance check outcome."""
    check = ComplianceCheck(**check_in.model_dump())
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


def get_compliance_check(db: Session, check_id: uuid.UUID) -> ComplianceCheck:
    """Retrieve a compliance check by primary key ID."""
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise NotFoundException(f"Compliance check with id '{check_id}' not found")
    return check


def get_compliance_checks(db: Session) -> List[ComplianceCheck]:
    """Retrieve all compliance checks."""
    statement = select(ComplianceCheck).order_by(ComplianceCheck.created_at.desc())
    return list(db.scalars(statement).all())


def delete_compliance_check(db: Session, check_id: uuid.UUID) -> None:
    """Delete a compliance check by primary key ID."""
    check = get_compliance_check(db, check_id)
    db.delete(check)
    db.commit()
