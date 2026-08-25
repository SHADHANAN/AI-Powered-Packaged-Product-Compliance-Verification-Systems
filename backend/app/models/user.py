from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.verification import Verification


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User account model representing system users, inspectors, and administrators."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.INSPECTOR,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    verifications: Mapped[List["Verification"]] = relationship(
        "Verification",
        back_populates="inspector",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
