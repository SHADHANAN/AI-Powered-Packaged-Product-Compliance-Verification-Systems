import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationCreate
from app.utils.exceptions import NotFoundException


def create_verification(db: Session, verification_in: VerificationCreate) -> Verification:
    """Create and persist a new verification record with foreign key validation and rollback protection."""
    # Foreign key validation for product_id
    if verification_in.product_id is not None:
        product = db.get(Product, verification_in.product_id)
        if not product:
            raise NotFoundException(f"Product with id '{verification_in.product_id}' not found")

    # Foreign key validation for inspector_id
    if verification_in.inspector_id is not None:
        inspector = db.get(User, verification_in.inspector_id)
        if not inspector:
            raise NotFoundException(f"User with id '{verification_in.inspector_id}' not found")

    verification = Verification(**verification_in.model_dump())
    db.add(verification)
    try:
        db.commit()
        db.refresh(verification)
        return verification
    except Exception:
        db.rollback()
        raise


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
    """Delete a verification by primary key ID with rollback protection."""
    verification = get_verification(db, verification_id)
    db.delete(verification)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
