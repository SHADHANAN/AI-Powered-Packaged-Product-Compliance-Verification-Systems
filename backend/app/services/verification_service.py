import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.verification import Verification
from app.schemas.verification import VerificationCreate
from app.utils.exceptions import NotFoundException


def create_verification(db: Session, verification_in: VerificationCreate) -> Verification:
    """Create and persist a new verification record."""
    verification = Verification(**verification_in.model_dump())
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def get_verification(db: Session, verification_id: uuid.UUID) -> Verification:
    """Retrieve a single verification by primary key ID."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")
    return verification


def get_verifications(db: Session) -> List[Verification]:
    """Retrieve all verification records."""
    statement = select(Verification).order_by(Verification.created_at.desc())
    return list(db.scalars(statement).all())


def delete_verification(db: Session, verification_id: uuid.UUID) -> None:
    """Delete a verification by primary key ID."""
    verification = get_verification(db, verification_id)
    db.delete(verification)
    db.commit()
