"""API endpoints for product packaging extraction and AI-assisted field interpretation."""
from typing import List
from fastapi import APIRouter, status

from app.schemas.extraction import FieldInterpretation, InterpretationRequest
from app.services.extraction_service.service import interpret_product_fields

router = APIRouter(tags=["Extraction"])


@router.post(
    "/interpret",
    response_model=List[FieldInterpretation],
    status_code=status.HTTP_200_OK,
    summary="Interpret OCR Fields",
    description="Analyze raw OCR text from packaging labels to interpret, correct, and normalize key product declarations with AI assistance.",
)
def interpret_ocr_fields_endpoint(
    request: InterpretationRequest,
) -> List[FieldInterpretation]:
    """Analyze raw OCR text, extract fields, and normalize/interpret using AI logic."""
    return interpret_product_fields(request.ocr_text)
