import os
import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import VerificationStatus
from app.models.extracted_field import ExtractedField
from app.models.verification import Verification
from app.services import field_extraction_service, ocr_service
from app.utils.exceptions import BadRequestException, NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.services.verification_pipeline")


def process_verification(db: Session, verification_id: uuid.UUID) -> Verification:
    """Execute the end-to-end OCR and Field Extraction pipeline for a verification record.
    
    1. Validates verification and image existence.
    2. Updates status to PROCESSING.
    3. Runs OCR text extraction.
    4. Extracts structured label fields.
    5. Cleans prior run artifacts and persists new ExtractedField records.
    6. Updates status to COMPLETED (or FAILED on error).
    """
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    image_path = verification.source_image_path
    if not image_path or not os.path.exists(image_path):
        logger.warning(f"Verification '{verification_id}' image file missing at '{image_path}'")
        raise BadRequestException("Associated product image file was not found on disk")

    # Update status to PROCESSING
    verification.status = VerificationStatus.PROCESSING
    db.commit()
    db.refresh(verification)

    try:
        # Step 1: Run OCR on preprocessed image
        raw_text = ocr_service.extract_text_from_image(image_path)
        verification.ocr_raw_text = raw_text

        # Step 2: Extract structured fields
        field_items = field_extraction_service.extract_fields_from_text(raw_text)

        # Step 3: Remove previously extracted fields for idempotent re-processing
        db.query(ExtractedField).filter(ExtractedField.verification_id == verification.id).delete()
        db.flush()

        # Step 4: Persist newly extracted fields
        for item in field_items:
            extracted_field = ExtractedField(
                verification_id=verification.id,
                field_name=item["field_name"],
                field_value=item["field_value"],
                confidence=item["confidence"],
                source_text=item["source_text"],
            )
            db.add(extracted_field)

        # Step 5: Mark verification as COMPLETED
        verification.status = VerificationStatus.COMPLETED
        verification.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(verification)
        logger.info(f"Verification '{verification_id}' pipeline completed successfully with {len(field_items)} fields")
        return verification

    except Exception as exc:
        db.rollback()
        logger.error(f"Verification '{verification_id}' processing failed: {exc}", exc_info=True)
        try:
            # Mark status as failed in a clean transaction
            failed_verification = db.get(Verification, verification_id)
            if failed_verification:
                failed_verification.status = VerificationStatus.FAILED
                db.commit()
        except Exception:
            db.rollback()
        raise


def get_verification_fields(db: Session, verification_id: uuid.UUID) -> List[ExtractedField]:
    """Retrieve all ExtractedField records belonging to a verification."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    statement = (
        select(ExtractedField)
        .where(ExtractedField.verification_id == verification_id)
        .order_by(ExtractedField.created_at.asc())
    )
    return list(db.scalars(statement).all())
