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


class CorrectiveRecommendationItem(BaseModel):
    """Actionable corrective recommendation for a single violation."""

    issue: str = Field(..., description="The compliance violation issue description.")
    recommendation: str = Field(..., description="AI-generated advisory corrective action.")
    supporting_evidence: str = Field(..., description="Extracted label snippet or rule evidence context.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score for the recommendation.")


class CorrectiveRecommendationsRead(BaseModel):
    """Structured list of AI-generated corrective recommendations."""

    verification_id: uuid.UUID = Field(..., description="ID of the verification run.")
    recommendations: List[CorrectiveRecommendationItem] = Field(default_factory=list, description="Advisory corrective guidance items.")
