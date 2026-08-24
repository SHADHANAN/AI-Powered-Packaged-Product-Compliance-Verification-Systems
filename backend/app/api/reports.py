import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import ReportCreate, ReportRead
from app.services import report_service

router = APIRouter(tags=["Reports"])


@router.post(
    "",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Report Record",
    description="Persist an exported compliance report record.",
)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
) -> ReportRead:
    return report_service.create_report(db=db, report_in=report_in)


@router.get(
    "",
    response_model=List[ReportRead],
    status_code=status.HTTP_200_OK,
    summary="List Reports",
    description="Retrieve all exported compliance report records.",
)
def list_reports(
    db: Session = Depends(get_db),
) -> List[ReportRead]:
    return report_service.get_reports(db=db)


@router.get(
    "/{id}",
    response_model=ReportRead,
    status_code=status.HTTP_200_OK,
    summary="Get Report",
    description="Retrieve a report record by unique identifier.",
)
def get_report(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ReportRead:
    return report_service.get_report(db=db, report_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Report Record",
    description="Delete a report record by unique identifier.",
)
def delete_report(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    report_service.delete_report(db=db, report_id=id)
