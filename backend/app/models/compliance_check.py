import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ComplianceStatus, Severity

if TYPE_CHECKING:
    from app.models.verification import Verification


class ComplianceCheck(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """ComplianceCheck model representing individual regulatory rule evaluation outcomes."""

    __tablename__ = "compliance_checks"
    __table_args__ = (
        Index("ix_compliance_checks_verification_rule", "verification_id", "rule_code"),
        Index("ix_compliance_checks_status_severity", "status", "severity"),
    )

    verification_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus, name="compliance_status", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        index=True,
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity_level", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        index=True,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    verification: Mapped["Verification"] = relationship("Verification", back_populates="compliance_checks")

    def __repr__(self) -> str:
        return f"<ComplianceCheck(id={self.id}, rule='{self.rule_code}', status='{self.status.value}')>"
