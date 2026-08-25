import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.models.enums import AuditAction, ComplianceStatus, ReportType, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.models.verification import Verification
from app.schemas.report import (
    ComplianceReportData,
    ReportCheck,
    ReportCreate,
    ReportField,
    ReportInspectorInfo,
    ReportProductInfo,
    ReportSummary,
    ReportViolation,
)
from app.services import audit_service
from app.utils.exceptions import BadRequestException, NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.services.report")


def generate_compliance_report(
    db: Session,
    verification_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> ComplianceReportData:
    """Generate or regenerate a structured compliance report from verification and evaluation records."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    # Validate that compliance checks have been performed
    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.verification_id == verification_id)
        .order_by(ComplianceCheck.created_at.asc())
    )
    compliance_checks = list(db.scalars(checks_stmt).all())
    if not compliance_checks:
        logger.warning(f"Attempted to generate report for un-evaluated verification '{verification_id}'")
        raise BadRequestException(
            "Compliance evaluation must be completed before generating a compliance report."
        )

    # Load extracted fields
    fields_stmt = (
        select(ExtractedField)
        .where(ExtractedField.verification_id == verification_id)
        .order_by(ExtractedField.created_at.asc())
    )
    extracted_fields = list(db.scalars(fields_stmt).all())

    # Load product and inspector entities if associated
    product_info: Optional[ReportProductInfo] = None
    if verification.product_id:
        product = db.get(Product, verification.product_id)
        if product:
            product_info = ReportProductInfo(
                id=product.id,
                product_name=product.product_name,
                brand_name=product.brand_name,
                manufacturer=product.manufacturer,
                importer=product.importer,
                country_of_origin=product.country_of_origin,
                net_quantity=product.net_quantity,
                quantity_unit=product.quantity_unit,
                batch_number=product.batch_number,
                manufacturing_date=product.manufacturing_date,
                import_date=product.import_date,
                mrp=float(product.mrp) if product.mrp is not None else None,
                customer_care_details=product.customer_care_details,
            )

    inspector_info: Optional[ReportInspectorInfo] = None
    if verification.inspector_id:
        inspector = db.get(User, verification.inspector_id)
        if inspector:
            inspector_info = ReportInspectorInfo(
                id=inspector.id,
                name=inspector.name,
                email=inspector.email,
                role=inspector.role,
            )

    # Construct report sub-structures
    report_fields = [
        ReportField(
            field_name=f.field_name,
            field_value=f.field_value or "",
            confidence=f.confidence,
            source_text=f.source_text,
        )
        for f in extracted_fields
    ]

    report_checks = [
        ReportCheck(
            rule_code=c.rule_code,
            rule_name=c.rule_name,
            status=c.status,
            severity=c.severity,
            message=c.message,
            expected_value=c.expected_value,
            actual_value=c.actual_value,
            recommendation=c.recommendation,
        )
        for c in compliance_checks
    ]

    violations = [
        ReportViolation(
            rule_code=c.rule_code,
            rule_name=c.rule_name,
            severity=c.severity,
            status=c.status,
            affected_field=c.rule_code.split("-")[1].lower() if "-" in c.rule_code else None,
            detected_value=c.actual_value,
            expected_requirement=c.expected_value,
            recommendation=c.recommendation,
        )
        for c in compliance_checks
        if c.status in (ComplianceStatus.FAIL, ComplianceStatus.WARNING)
    ]

    recommendations = [c.recommendation for c in compliance_checks if c.recommendation]

    passed_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.PASS)
    failed_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.FAIL)
    warning_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.WARNING)
    na_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.NOT_APPLICABLE)

    summary = ReportSummary(
        total_rules=len(compliance_checks),
        passed_rules=passed_count,
        failed_rules=failed_count,
        warning_rules=warning_count,
        not_applicable_rules=na_count,
        overall_score=verification.overall_score,
    )

    try:
        # Idempotent persistence of Report record
        existing_report = (
            db.query(Report)
            .filter(Report.verification_id == verification_id, Report.report_type == ReportType.PDF)
            .first()
        )
        if not existing_report:
            existing_report = Report(
                verification_id=verification_id,
                report_type=ReportType.PDF,
                file_path=f"reports/compliance_report_{verification_id}.pdf",
            )
            db.add(existing_report)
        else:
            existing_report.generated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(existing_report)

        # Record audit log
        audit_service.create_audit_log(
            db=db,
            verification_id=verification_id,
            user_id=user_id or verification.inspector_id,
            action=AuditAction.REPORT_GENERATED,
            status="SUCCESS",
            details=f"Compliance report generated with score {verification.overall_score}%",
        )

        logger.info(f"Generated report '{existing_report.id}' for verification '{verification_id}'")

        return ComplianceReportData(
            report_id=existing_report.id,
            verification_id=verification_id,
            generated_at=existing_report.generated_at,
            verification_status=verification.status,
            overall_score=verification.overall_score,
            product=product_info,
            inspector=inspector_info,
            summary=summary,
            extracted_fields=report_fields,
            checks=report_checks,
            violations=violations,
            recommendations=recommendations,
        )

    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to generate report for verification '{verification_id}': {exc}", exc_info=True)
        raise


def get_latest_compliance_report(
    db: Session,
    verification_id: uuid.UUID,
) -> ComplianceReportData:
    """Retrieve the latest generated structured compliance report."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    report_record = (
        db.query(Report)
        .filter(Report.verification_id == verification_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if not report_record:
        raise NotFoundException(f"No generated report found for verification '{verification_id}'")

    # Load compliance checks
    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.verification_id == verification_id)
        .order_by(ComplianceCheck.created_at.asc())
    )
    compliance_checks = list(db.scalars(checks_stmt).all())

    # Load extracted fields
    fields_stmt = (
        select(ExtractedField)
        .where(ExtractedField.verification_id == verification_id)
        .order_by(ExtractedField.created_at.asc())
    )
    extracted_fields = list(db.scalars(fields_stmt).all())

    product_info: Optional[ReportProductInfo] = None
    if verification.product_id:
        product = db.get(Product, verification.product_id)
        if product:
            product_info = ReportProductInfo(
                id=product.id,
                product_name=product.product_name,
                brand_name=product.brand_name,
                manufacturer=product.manufacturer,
                importer=product.importer,
                country_of_origin=product.country_of_origin,
                net_quantity=product.net_quantity,
                quantity_unit=product.quantity_unit,
                batch_number=product.batch_number,
                manufacturing_date=product.manufacturing_date,
                import_date=product.import_date,
                mrp=float(product.mrp) if product.mrp is not None else None,
                customer_care_details=product.customer_care_details,
            )

    inspector_info: Optional[ReportInspectorInfo] = None
    if verification.inspector_id:
        inspector = db.get(User, verification.inspector_id)
        if inspector:
            inspector_info = ReportInspectorInfo(
                id=inspector.id,
                name=inspector.name,
                email=inspector.email,
                role=inspector.role,
            )

    report_fields = [
        ReportField(
            field_name=f.field_name,
            field_value=f.field_value or "",
            confidence=f.confidence,
            source_text=f.source_text,
        )
        for f in extracted_fields
    ]

    report_checks = [
        ReportCheck(
            rule_code=c.rule_code,
            rule_name=c.rule_name,
            status=c.status,
            severity=c.severity,
            message=c.message,
            expected_value=c.expected_value,
            actual_value=c.actual_value,
            recommendation=c.recommendation,
        )
        for c in compliance_checks
    ]

    violations = [
        ReportViolation(
            rule_code=c.rule_code,
            rule_name=c.rule_name,
            severity=c.severity,
            status=c.status,
            affected_field=c.rule_code.split("-")[1].lower() if "-" in c.rule_code else None,
            detected_value=c.actual_value,
            expected_requirement=c.expected_value,
            recommendation=c.recommendation,
        )
        for c in compliance_checks
        if c.status in (ComplianceStatus.FAIL, ComplianceStatus.WARNING)
    ]

    recommendations = [c.recommendation for c in compliance_checks if c.recommendation]

    passed_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.PASS)
    failed_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.FAIL)
    warning_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.WARNING)
    na_count = sum(1 for c in compliance_checks if c.status == ComplianceStatus.NOT_APPLICABLE)

    summary = ReportSummary(
        total_rules=len(compliance_checks),
        passed_rules=passed_count,
        failed_rules=failed_count,
        warning_rules=warning_count,
        not_applicable_rules=na_count,
        overall_score=verification.overall_score,
    )

    return ComplianceReportData(
        report_id=report_record.id,
        verification_id=verification_id,
        generated_at=report_record.generated_at,
        verification_status=verification.status,
        overall_score=verification.overall_score,
        product=product_info,
        inspector=inspector_info,
        summary=summary,
        extracted_fields=report_fields,
        checks=report_checks,
        violations=violations,
        recommendations=recommendations,
    )


# ----------------------------------------------------------------------
# GENERIC CRUD REPORT OPERATIONS
# ----------------------------------------------------------------------

def create_report(db: Session, report_in: ReportCreate) -> Report:
    """Create and persist a report metadata record with parent verification validation."""
    verification = db.get(Verification, report_in.verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{report_in.verification_id}' not found")

    report = Report(**report_in.model_dump())
    db.add(report)
    try:
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise


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
    """Delete a report record by primary key ID with rollback protection."""
    report = get_report(db, report_id)
    db.delete(report)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
