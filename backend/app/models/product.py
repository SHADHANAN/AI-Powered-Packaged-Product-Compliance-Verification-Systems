from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.verification import Verification


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Product model representing packaged commodities subjected to compliance inspection."""

    __tablename__ = "products"

    product_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    importer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    net_quantity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    import_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mrp: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    customer_care_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    verifications: Mapped[List["Verification"]] = relationship(
        "Verification",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.product_name}', brand='{self.brand_name}')>"
