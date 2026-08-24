import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base schema for product data."""

    product_name: Optional[str] = Field(default=None, max_length=255)
    brand_name: Optional[str] = Field(default=None, max_length=255)
    manufacturer: Optional[str] = Field(default=None, max_length=500)
    importer: Optional[str] = Field(default=None, max_length=500)
    country_of_origin: Optional[str] = Field(default=None, max_length=100)
    net_quantity: Optional[str] = Field(default=None, max_length=100)
    quantity_unit: Optional[str] = Field(default=None, max_length=50)
    batch_number: Optional[str] = Field(default=None, max_length=100)
    manufacturing_date: Optional[date] = None
    import_date: Optional[date] = None
    mrp: Optional[Decimal] = Field(default=None, ge=0)
    customer_care_details: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product entry."""
    pass


class ProductUpdate(ProductBase):
    """Schema for updating product entry."""
    pass


class ProductRead(ProductBase):
    """Schema for reading product data from database."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
