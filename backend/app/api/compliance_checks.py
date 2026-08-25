import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.compliance_check import ComplianceCheckCreate, ComplianceCheckRead
from app.services import compliance_check_service

router = APIRouter(tags=["Compliance Checks"])


@router.post(
    "",
    response_model=ComplianceCheckRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Compliance Check",
    description="Persist a compliance rule check outcome.",
)
def create_compliance_check(
    check_in: ComplianceCheckCreate,
    db: Session = Depends(get_db),
) -> ComplianceCheckRead:
    return compliance_check_service.create_compliance_check(db=db, check_in=check_in)


@router.get(
    "",
    response_model=List[ComplianceCheckRead],
    status_code=status.HTTP_200_OK,
    summary="List Compliance Checks",
    description="Retrieve all compliance check outcomes.",
)
def list_compliance_checks(
    db: Session = Depends(get_db),
) -> List[ComplianceCheckRead]:
    return compliance_check_service.get_compliance_checks(db=db)


@router.get(
    "/{id}",
    response_model=ComplianceCheckRead,
    status_code=status.HTTP_200_OK,
    summary="Get Compliance Check",
    description="Retrieve a compliance check outcome by unique identifier.",
)
def get_compliance_check(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ComplianceCheckRead:
    return compliance_check_service.get_compliance_check(db=db, check_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Compliance Check",
    description="Delete a compliance check outcome by unique identifier.",
)
def delete_compliance_check(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    compliance_check_service.delete_compliance_check(db=db, check_id=id)
