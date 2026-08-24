import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.extracted_field import ExtractedFieldCreate, ExtractedFieldRead
from app.services import extracted_field_service

router = APIRouter(tags=["Extracted Fields"])


@router.post(
    "",
    response_model=ExtractedFieldRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Extracted Field",
    description="Persist an extracted OCR field entry.",
)
def create_extracted_field(
    field_in: ExtractedFieldCreate,
    db: Session = Depends(get_db),
) -> ExtractedFieldRead:
    return extracted_field_service.create_extracted_field(db=db, field_in=field_in)


@router.get(
    "",
    response_model=List[ExtractedFieldRead],
    status_code=status.HTTP_200_OK,
    summary="List Extracted Fields",
    description="Retrieve all extracted OCR fields.",
)
def list_extracted_fields(
    db: Session = Depends(get_db),
) -> List[ExtractedFieldRead]:
    return extracted_field_service.get_extracted_fields(db=db)


@router.get(
    "/{id}",
    response_model=ExtractedFieldRead,
    status_code=status.HTTP_200_OK,
    summary="Get Extracted Field",
    description="Retrieve an extracted field by unique identifier.",
)
def get_extracted_field(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ExtractedFieldRead:
    return extracted_field_service.get_extracted_field(db=db, field_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Extracted Field",
    description="Delete an extracted field by unique identifier.",
)
def delete_extracted_field(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    extracted_field_service.delete_extracted_field(db=db, field_id=id)
