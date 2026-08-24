import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VerificationStatus

if TYPE_CHECKING:
    from app.models.compliance_check import ComplianceCheck
    from app.models.extracted_field import ExtractedField
    from app.models.product import Product
    from app.models.report import Report
    from app.models.user import User


class Verification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Verification model representing one packaged commodity inspection run."""

    __tablename__ = "verifications"
    __table_args__ = (
        CheckConstraint("overall_score >= 0.0 AND overall_score <= 100.0", name="ck_verification_overall_score"),
        Index("ix_verifications_status_created_at", "status", "created_at"),
    )

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    inspector_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=VerificationStatus.PENDING,
        index=True,
        nullable=False,
    )
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_image_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    ocr_raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="verifications")
    inspector: Mapped[Optional["User"]] = relationship("User", back_populates="verifications")
    extracted_fields: Mapped[List["ExtractedField"]] = relationship(
        "ExtractedField",
        back_populates="verification",
        cascade="all, delete-orphan",
    )
    compliance_checks: Mapped[List["ComplianceCheck"]] = relationship(
        "ComplianceCheck",
        back_populates="verification",
        cascade="all, delete-orphan",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="verification",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Verification(id={self.id}, status='{self.status.value}', score={self.overall_score})>"
