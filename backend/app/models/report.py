import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import ReportType

if TYPE_CHECKING:
    from app.models.verification import Verification


class Report(Base, UUIDPrimaryKeyMixin):
    """Report model representing generated compliance report files (PDF/Excel)."""

    __tablename__ = "reports"

    verification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, name="report_type", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    verification: Mapped["Verification"] = relationship("Verification", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type='{self.report_type.value}', path='{self.file_path}')>"
