"""Schemas for product field extraction and AI-assisted OCR interpretation."""
from typing import Optional
from pydantic import BaseModel, Field


class InterpretationRequest(BaseModel):
    """Request payload for OCR field interpretation."""

    ocr_text: str = Field(..., description="Raw OCR text extracted from product label packaging.")


class FieldInterpretation(BaseModel):
    """Structured AI-interpreted / normalized field representation."""

    field: str = Field(..., description="Target field name (e.g. mrp, net_quantity).")
    original_ocr_value: Optional[str] = Field(default=None, description="Original raw value parsed by regex pattern matching.")
    interpreted_value: Optional[str] = Field(default=None, description="Cleaned, parsed, or normalized value from AI model.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of interpretation (between 0.0 and 1.0).")
    evidence: Optional[str] = Field(default=None, description="Source context snippet from the raw OCR text.")
    short_reason: str = Field(..., description="Short explanation of how this value was normalized or flagged.")
    status: str = Field(..., description="Status of the interpretation (e.g. COMPLETED, NEEDS_REVIEW, UNRESOLVED).")
