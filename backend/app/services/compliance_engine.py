import uuid
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.compliance_check import ComplianceCheck
from app.models.enums import AuditAction, ComplianceStatus, Severity, VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.verification import Verification
from app.schemas.compliance_check import ComplianceCheckRead, ComplianceSummaryRead
from app.services import audit_service
from app.services.compliance_rules import ALL_RULES, RuleEvaluationResult
from app.utils.exceptions import NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.services.compliance_engine")

# Weight mapping by severity level for deterministic score computation
SEVERITY_WEIGHTS: Dict[Severity, float] = {
    Severity.CRITICAL: 4.0,
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 1.0,
}


def calculate_compliance_score(results: List[RuleEvaluationResult]) -> float:
    """Calculate deterministic compliance percentage score based on rule outcomes and severities."""
    passed_weight = 0.0
    applicable_weight = 0.0

    for result in results:
        weight = SEVERITY_WEIGHTS.get(result.severity, 1.0)
        if result.status == ComplianceStatus.PASS:
            passed_weight += weight
            applicable_weight += weight
        elif result.status == ComplianceStatus.WARNING:
            passed_weight += (0.5 * weight)
            applicable_weight += weight
        elif result.status == ComplianceStatus.FAIL:
            applicable_weight += weight
        elif result.status == ComplianceStatus.NOT_APPLICABLE:
            # Excluded from both numerator and denominator
            continue

    if applicable_weight == 0.0:
        return 100.0

    score = round((passed_weight / applicable_weight) * 100.0, 2)
    return max(0.0, min(100.0, score))


def evaluate_verification_compliance(
    db: Session,
    verification_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> ComplianceSummaryRead:
    """Evaluate compliance rules against extracted fields for a verification run."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    # Load extracted fields
    extracted_fields_stmt = select(ExtractedField).where(ExtractedField.verification_id == verification_id)
    extracted_fields = list(db.scalars(extracted_fields_stmt).all())

    # Build field mapping dictionary
    field_map: Dict[str, str] = {f.field_name: f.field_value for f in extracted_fields}

    # Evaluate all registered Legal Metrology rules
    evaluation_results: List[RuleEvaluationResult] = [
        rule.evaluate(field_map) for rule in ALL_RULES
    ]

    # Calculate overall compliance score
    overall_score = calculate_compliance_score(evaluation_results)

    try:
        # 1. Clean up existing compliance check records for idempotency
        db.query(ComplianceCheck).filter(ComplianceCheck.verification_id == verification_id).delete()
        db.flush()

        # 2. Persist new ComplianceCheck records
        created_checks: List[ComplianceCheck] = []
        for res in evaluation_results:
            check = ComplianceCheck(
                verification_id=verification_id,
                rule_code=res.rule_code,
                rule_name=res.rule_name,
                status=res.status,
                severity=res.severity,
                message=res.message,
                expected_value=res.expected_value,
                actual_value=res.actual_value,
                recommendation=res.recommendation,
            )
            db.add(check)
            created_checks.append(check)

        # 3. Update Verification entity
        verification.overall_score = overall_score
        verification.status = VerificationStatus.COMPLETED
        db.commit()
        db.refresh(verification)

        for check in created_checks:
            db.refresh(check)

        # 4. Record audit log
        audit_service.create_audit_log(
            db=db,
            verification_id=verification.id,
            user_id=user_id or verification.inspector_id,
            action=AuditAction.COMPLIANCE_CHECKED,
            status="SUCCESS",
            details=f"Evaluated {len(evaluation_results)} compliance rules, overall score: {overall_score}%",
        )

        logger.info(
            f"Evaluated verification '{verification_id}': score={overall_score}%, total_rules={len(evaluation_results)}"
        )

        return build_compliance_summary(verification, created_checks)

    except Exception as exc:
        db.rollback()
        logger.error(f"Compliance evaluation failed for verification '{verification_id}': {exc}", exc_info=True)
        raise


def get_verification_compliance_summary(db: Session, verification_id: uuid.UUID) -> ComplianceSummaryRead:
    """Retrieve existing compliance evaluation results for a verification run."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.verification_id == verification_id)
        .order_by(ComplianceCheck.created_at.asc())
    )
    checks = list(db.scalars(checks_stmt).all())

    return build_compliance_summary(verification, checks)


def build_compliance_summary(
    verification: Verification,
    checks: List[ComplianceCheck],
) -> ComplianceSummaryRead:
    """Helper to transform ComplianceCheck records into a structured summary schema."""
    passed_count = sum(1 for c in checks if c.status == ComplianceStatus.PASS)
    failed_count = sum(1 for c in checks if c.status == ComplianceStatus.FAIL)
    warning_count = sum(1 for c in checks if c.status == ComplianceStatus.WARNING)
    na_count = sum(1 for c in checks if c.status == ComplianceStatus.NOT_APPLICABLE)

    check_reads = [ComplianceCheckRead.model_validate(c) for c in checks]
    violations = [c for c in check_reads if c.status in (ComplianceStatus.FAIL, ComplianceStatus.WARNING)]
    recommendations = [c.recommendation for c in check_reads if c.recommendation]

    return ComplianceSummaryRead(
        verification_id=verification.id,
        overall_score=verification.overall_score,
        status=verification.status,
        total_rules=len(checks),
        passed_rules=passed_count,
        failed_rules=failed_count,
        warning_rules=warning_count,
        not_applicable_rules=na_count,
        violations=violations,
        recommendations=recommendations,
        checks=check_reads,
    )
