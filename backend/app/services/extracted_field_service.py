import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extracted_field import ExtractedField
from app.schemas.extracted_field import ExtractedFieldCreate
from app.utils.exceptions import NotFoundException


def create_extracted_field(db: Session, field_in: ExtractedFieldCreate) -> ExtractedField:
    """Create and persist an extracted OCR field."""
    field = ExtractedField(**field_in.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def get_extracted_field(db: Session, field_id: uuid.UUID) -> ExtractedField:
    """Retrieve an extracted field by primary key ID."""
    field = db.get(ExtractedField, field_id)
    if not field:
        raise NotFoundException(f"Extracted field with id '{field_id}' not found")
    return field


def get_extracted_fields(db: Session) -> List[ExtractedField]:
    """Retrieve all extracted fields."""
    statement = select(ExtractedField).order_by(ExtractedField.created_at.desc())
    return list(db.scalars(statement).all())


def delete_extracted_field(db: Session, field_id: uuid.UUID) -> None:
    """Delete an extracted field by primary key ID."""
    field = get_extracted_field(db, field_id)
    db.delete(field)
    db.commit()
