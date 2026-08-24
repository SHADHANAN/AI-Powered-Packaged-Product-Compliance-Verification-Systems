import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.verification import Verification


class ExtractedField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ExtractedField model representing key-value evidence extracted from product packaging."""

    __tablename__ = "extracted_fields"
    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_extracted_field_confidence"),
        Index("ix_extracted_fields_verification_field_name", "verification_id", "field_name"),
    )

    verification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    field_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    verification: Mapped["Verification"] = relationship("Verification", back_populates="extracted_fields")

    def __repr__(self) -> str:
        return f"<ExtractedField(id={self.id}, name='{self.field_name}', confidence={self.confidence})>"
