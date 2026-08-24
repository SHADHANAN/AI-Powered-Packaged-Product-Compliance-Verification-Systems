import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate
from app.utils.exceptions import NotFoundException


def create_report(db: Session, report_in: ReportCreate) -> Report:
    """Create and persist a report metadata record."""
    report = Report(**report_in.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: uuid.UUID) -> Report:
    """Retrieve a report metadata record by primary key ID."""
    report = db.get(Report, report_id)
    if not report:
        raise NotFoundException(f"Report with id '{report_id}' not found")
    return report


def get_reports(db: Session) -> List[Report]:
    """Retrieve all report records."""
    statement = select(Report).order_by(Report.generated_at.desc())
    return list(db.scalars(statement).all())


def delete_report(db: Session, report_id: uuid.UUID) -> None:
    """Delete a report record by primary key ID."""
    report = get_report(db, report_id)
    db.delete(report)
    db.commit()
