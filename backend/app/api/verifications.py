import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.verification import VerificationCreate, VerificationRead
from app.services import verification_service

router = APIRouter(tags=["Verifications"])


@router.post(
    "",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Verification",
    description="Initiate a new product compliance verification run.",
)
def create_verification(
    verification_in: VerificationCreate,
    db: Session = Depends(get_db),
) -> VerificationRead:
    return verification_service.create_verification(db=db, verification_in=verification_in)


@router.get(
    "",
    response_model=List[VerificationRead],
    status_code=status.HTTP_200_OK,
    summary="List Verifications",
    description="Retrieve all product compliance verification runs.",
)
def list_verifications(
    db: Session = Depends(get_db),
) -> List[VerificationRead]:
    return verification_service.get_verifications(db=db)


@router.get(
    "/{id}",
    response_model=VerificationRead,
    status_code=status.HTTP_200_OK,
    summary="Get Verification",
    description="Retrieve a verification run by unique identifier.",
)
def get_verification(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> VerificationRead:
    return verification_service.get_verification(db=db, verification_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Verification",
    description="Delete a verification run by unique identifier.",
)
def delete_verification(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    verification_service.delete_verification(db=db, verification_id=id)
