"""Schemas for Legal Metrology compliance verification and explanations."""
import uuid
from typing import List
from pydantic import BaseModel, Field


class ComplianceExplanationRead(BaseModel):
    """Structured AI-generated compliance explanation and results summary."""

    verification_id: uuid.UUID = Field(..., description="ID of the verification run.")
    status: str = Field(..., description="Deterministic compliance status (COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT).")
    score: float = Field(..., description="Overall compliance score (between 0.0 and 100.0).")
    explanation: str = Field(..., description="Clear human-readable regulatory compliance explanation.")
    violations: List[str] = Field(default_factory=list, description="List of rule codes and violation messages.")
