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
from app.config import get_settings
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

    # Evaluate compliance rules
    evaluation_results: List[RuleEvaluationResult] = []
    ai_success = False

    ai_status = "DISABLED"
    fallback_used = False
    decision_source = "Deterministic Engine"

    settings = get_settings()
    if settings.AI_ENABLED:
        try:
            from app.ai.security import validate_untrusted_text, PromptInjectionException, record_security_event
            # 1. Prompt Injection check
            try:
                for key, val in field_map.items():
                    if val:
                        validate_untrusted_text(str(val), context=f"Compliance field '{key}'")
            except PromptInjectionException as e:
                ai_status = "PROMPT_INJECTION_BLOCKED"
                record_security_event(db, verification_id, details="Prompt injection attempt blocked during compliance evaluation.")
                raise e

            # 2. Call AI service
            from app.services.ai_service import AIService
            ai_evaluations = AIService().evaluate_compliance(field_map, ALL_RULES)
            
            # 3. Validate AI evaluations structure and confidence
            if not ai_evaluations or not isinstance(ai_evaluations, list):
                raise ValueError("validation failure: AI response did not return a valid list of rule evaluations")
                
            for item in ai_evaluations:
                if not isinstance(item, dict):
                    raise ValueError("validation failure: AI response item is not a dictionary")
                
                # Check confidence threshold (low confidence check)
                if "confidence" in item:
                    try:
                        conf_val = float(item["confidence"])
                        if conf_val < 0.7:
                            raise ValueError("low confidence: AI confidence score is below threshold")
                    except (TypeError, ValueError) as c_err:
                        if "low confidence" in str(c_err):
                            raise c_err
                
                # Check required rule fields
                rule_code = item.get("rule_code")
                status_str = item.get("status")
                if not rule_code:
                    raise ValueError("validation failure: missing rule_code in AI response")
                if not status_str or status_str.upper() not in ["PASS", "FAIL", "WARNING", "NOT_APPLICABLE"]:
                    raise ValueError("validation failure: invalid status in AI response")
            
            # 4. Map evaluations to RuleEvaluationResult
            for item in ai_evaluations:
                status_str = item.get("status", "warning").lower()
                try:
                    status_enum = ComplianceStatus(status_str)
                except ValueError:
                    status_enum = ComplianceStatus.WARNING
                    
                severity_str = item.get("severity", "low").lower()
                try:
                    severity_enum = Severity(severity_str)
                except ValueError:
                    severity_enum = Severity.LOW
                    
                evaluation_results.append(
                    RuleEvaluationResult(
                        rule_code=item.get("rule_code", "UNKNOWN"),
                        rule_name=item.get("rule_name", "Unknown AI Rule"),
                        status=status_enum,
                        severity=severity_enum,
                        message=item.get("message", "Evaluated by AI"),
                        expected_value=item.get("expected_value"),
                        actual_value=item.get("actual_value"),
                        recommendation=item.get("recommendation"),
                    )
                )
            
            if evaluation_results:
                ai_success = True
                ai_status = "SUCCESS"
                fallback_used = False
                decision_source = "AI Assistant"
                logger.info(f"AI compliance evaluation successful for verification '{verification_id}'")
        except Exception as e:
            fallback_used = True
            decision_source = "Deterministic Engine (Fallback)"
            
            # Map exception to appropriate ai_status
            import json
            err_str = str(e).lower()
            if "timeout" in err_str:
                ai_status = "TIMEOUT"
            elif "unavailable" in err_str or "connection" in err_str or "http" in err_str or "request failed" in err_str:
                ai_status = "API_UNAVAILABLE"
            elif isinstance(e, json.JSONDecodeError) or "json" in err_str or "decode" in err_str or "malformed" in err_str or "expecting value" in err_str:
                ai_status = "MALFORMED_JSON"
            elif "validation failure" in err_str:
                ai_status = "VALIDATION_FAILURE"
            elif "low confidence" in err_str:
                ai_status = "LOW_CONFIDENCE"
            elif "prompt injection" in err_str or "security validation failed" in err_str:
                ai_status = "PROMPT_INJECTION_BLOCKED"
            else:
                ai_status = "PROVIDER_ERROR"
                
            logger.warning(
                f"AI compliance evaluation failed ({ai_status}) for verification '{verification_id}', falling back to deterministic engine: {e}",
                exc_info=True
            )
            evaluation_results = []

    if not ai_success:
        # Fallback to deterministic evaluation
        logger.info(f"Using deterministic compliance engine for verification '{verification_id}'")
        evaluation_results = [
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
        # Set AI tracking attributes
        verification.ai_status = ai_status
        verification.fallback_used = fallback_used
        verification.decision_source = decision_source
        
        has_fail = any(c.status == ComplianceStatus.FAIL for c in created_checks)
        has_warn = any(c.status == ComplianceStatus.WARNING for c in created_checks)
        if has_fail or has_warn:
            verification.final_result = "NON_COMPLIANT"
        else:
            verification.final_result = "COMPLIANT"

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

    # Calculate final_result if not set (or use model attribute)
    final_res = getattr(verification, "final_result", None)
    if not final_res:
        if failed_count > 0 or warning_count > 0:
            final_res = "NON_COMPLIANT"
        else:
            final_res = "COMPLIANT"

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
        ai_status=getattr(verification, "ai_status", "DISABLED") or "DISABLED",
        fallback_used=bool(getattr(verification, "fallback_used", False)),
        decision_source=getattr(verification, "decision_source", "Deterministic Engine") or "Deterministic Engine",
        final_result=final_res,
    )
