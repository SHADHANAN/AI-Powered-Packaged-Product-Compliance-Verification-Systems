import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.authorization import (
    require_authenticated_user,
    require_inspector,
    verify_verification_ownership,
)
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.enums import AuditAction
from app.models.user import User
from app.models.verification import Verification
from app.schemas.audit_log import AuditLogRead
from app.schemas.compliance import ComplianceExplanationRead, CorrectiveRecommendationsRead, AnomalyDetectionRead
from app.schemas.compliance_check import ComplianceSummaryRead
from app.schemas.extracted_field import ExtractedFieldRead
from app.schemas.report import ComplianceReportData
from app.schemas.verification import VerificationCreate, VerificationRead
from app.services import (
    audit_service,
    compliance_engine,
    image_service,
    pdf_report_service,
    report_service,
    verification_pipeline_service,
    verification_service,
)
from app.utils.exceptions import NotFoundException
from app.utils.file_validation import validate_image_file

router = APIRouter(tags=["Verifications"])


@router.post(
    "/upload",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Packaged Product Image",
    description="Securely upload a packaged product image, validate integrity, store safely, and register a new Verification record.",
)
def upload_verification_image(
    file: UploadFile = File(..., description="Packaged product image file (JPG, PNG, WebP, max 10MB)"),
    product_id: Optional[uuid.UUID] = Form(default=None, description="Optional associated product ID"),
    current_user: User = Depends(require_inspector),
    db: Session = Depends(get_db),
) -> VerificationRead:
    """Validate, store, and create a Verification record for an uploaded product image."""
    # 1. Validate image format, MIME type, size, and binary integrity
    image_bytes = validate_image_file(file)

    # 2. Persist image with sanitized UUID filename
    stored_path = image_service.save_image_file(
        content=image_bytes,
        original_filename=file.filename or "image.jpg",
    )

    # 3. Create Verification record; safely clean up file if database transaction fails
    try:
        verification_in = VerificationCreate(
            source_image_path=stored_path,
            product_id=product_id,
            inspector_id=current_user.id,
        )
        created_verification = verification_service.create_verification(db=db, verification_in=verification_in)

        # 4. Record audit event
        audit_service.create_audit_log(
            db=db,
            verification_id=created_verification.id,
            user_id=current_user.id,
            action=AuditAction.IMAGE_UPLOADED,
            status="SUCCESS",
            details=f"Uploaded product image '{file.filename}' ({len(image_bytes)} bytes)",
        )

        return created_verification
    except Exception:
        image_service.delete_image_file(stored_path)
        raise


@router.post(
    "/{id}/process",
    response_model=VerificationRead,
    status_code=status.HTTP_200_OK,
    summary="Process Verification Pipeline",
    description="Run OCR and structured field extraction pipeline on a stored verification image.",
)
def process_verification_pipeline(
    id: uuid.UUID,
    current_user: User = Depends(require_inspector),
    db: Session = Depends(get_db),
) -> VerificationRead:
    """Execute OCR and field extraction on an existing verification image."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return verification_pipeline_service.process_verification(db=db, verification_id=id)


@router.get(
    "/{id}/fields",
    response_model=List[ExtractedFieldRead],
    status_code=status.HTTP_200_OK,
    summary="Get Extracted Fields for Verification",
    description="Retrieve all extracted label fields associated with a specific verification.",
)
def get_verification_extracted_fields(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> List[ExtractedFieldRead]:
    """Retrieve all ExtractedField records created for a verification run."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return verification_pipeline_service.get_verification_fields(db=db, verification_id=id)


@router.post(
    "/{id}/compliance",
    response_model=ComplianceSummaryRead,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Product Compliance",
    description="Evaluate extracted product label fields against Legal Metrology compliance rules and calculate overall score.",
)
def evaluate_compliance(
    id: uuid.UUID,
    current_user: User = Depends(require_inspector),
    db: Session = Depends(get_db),
) -> ComplianceSummaryRead:
    """Run Legal Metrology rule evaluation engine on verification fields."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return compliance_engine.evaluate_verification_compliance(
        db=db,
        verification_id=id,
        user_id=current_user.id,
    )


@router.get(
    "/{id}/compliance",
    response_model=ComplianceSummaryRead,
    status_code=status.HTTP_200_OK,
    summary="Get Compliance Evaluation Results",
    description="Retrieve evaluated Legal Metrology rule check results, overall score, and recommendations for a verification run.",
)
def get_compliance_results(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplianceSummaryRead:
    """Retrieve existing compliance check outcomes and overall compliance score."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return compliance_engine.get_verification_compliance_summary(db=db, verification_id=id)


@router.get(
    "/{id}/compliance/explain",
    response_model=ComplianceExplanationRead,
    status_code=status.HTTP_200_OK,
    summary="Get AI-generated Compliance Explanation",
    description="Retrieve an AI-generated regulatory explanation of the compliance status and violations for a verification run.",
)
def get_compliance_explanation(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplianceExplanationRead:
    """Generate or retrieve AI-assisted regulatory compliance explanation."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    
    from app.ai.explanation import generate_ai_compliance_explanation
    return generate_ai_compliance_explanation(db=db, verification_id=id)


@router.get(
    "/{id}/compliance/recommendations",
    response_model=CorrectiveRecommendationsRead,
    status_code=status.HTTP_200_OK,
    summary="Get AI-generated Compliance Recommendations",
    description="Retrieve AI-generated corrective packaging recommendations based strictly on deterministic compliance violations.",
)
def get_compliance_recommendations(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> CorrectiveRecommendationsRead:
    """Generate or retrieve AI-assisted regulatory compliance corrective recommendations."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    
    from app.ai.recommendation import generate_ai_corrective_recommendations
    recs = generate_ai_corrective_recommendations(db=db, verification_id=id)
    return {
        "verification_id": id,
        "recommendations": recs
    }


@router.get(
    "/{id}/anomalies",
    response_model=AnomalyDetectionRead,
    status_code=status.HTTP_200_OK,
    summary="Get AI-assisted Product Label Anomalies",
    description="Retrieve AI-assisted product packaging label anomaly audit findings based on extracted fields and OCR text (advisory only).",
)
def get_label_anomalies(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> AnomalyDetectionRead:
    """Retrieve AI-assisted product label anomaly audit findings."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    
    from app.ai.anomaly import generate_ai_anomaly_detection
    anomalies = generate_ai_anomaly_detection(db=db, verification_id=id)
    return {
        "verification_id": id,
        "anomalies": anomalies
    }


@router.post(
    "/{id}/report",
    response_model=ComplianceReportData,
    status_code=status.HTTP_200_OK,
    summary="Generate Compliance Report",
    description="Generate or regenerate an audit-ready structured compliance report for a verification run.",
)
def generate_report(
    id: uuid.UUID,
    current_user: User = Depends(require_inspector),
    db: Session = Depends(get_db),
) -> ComplianceReportData:
    """Generate or update the compliance report for an evaluated verification."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return report_service.generate_compliance_report(
        db=db,
        verification_id=id,
        user_id=current_user.id,
    )


@router.get(
    "/{id}/report",
    response_model=ComplianceReportData,
    status_code=status.HTTP_200_OK,
    summary="Get Compliance Report",
    description="Retrieve the latest generated structured compliance report for a verification run.",
)
def get_report(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> ComplianceReportData:
    """Retrieve the latest compliance report for a verification."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return report_service.get_latest_compliance_report(db=db, verification_id=id)


@router.get(
    "/{id}/report/pdf",
    status_code=status.HTTP_200_OK,
    summary="Export Compliance Report as PDF",
    description="Export the evaluated verification compliance report as an audit-grade PDF document.",
)
def export_compliance_report_pdf(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and stream a publication-grade PDF compliance report."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    pdf_stream = pdf_report_service.generate_compliance_pdf(
        db=db,
        verification_id=id,
        user_id=current_user.id,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="compliance_report_{id}.pdf"',
    }
    return StreamingResponse(
        content=pdf_stream,
        media_type="application/pdf",
        headers=headers,
    )


@router.get(
    "/{id}/audit-logs",
    response_model=List[AuditLogRead],
    status_code=status.HTTP_200_OK,
    summary="Get Verification Audit Trail",
    description="Retrieve chronological audit log events recorded for a verification run.",
)
def get_audit_trail(
    id: uuid.UUID,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
) -> List[AuditLogRead]:
    """Retrieve chronological audit trail entries for a verification run."""
    verification = db.get(Verification, id)
    if not verification:
        raise NotFoundException(f"Verification with id '{id}' not found")
    verify_verification_ownership(verification, current_user)
    return audit_service.get_verification_audit_logs(db=db, verification_id=id)


@router.post(
    "",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Verification",
    description="Initiate a new product compliance verification run directly.",
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
