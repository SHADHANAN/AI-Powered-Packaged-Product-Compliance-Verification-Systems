import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate
from app.utils.exceptions import NotFoundException


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """Create and persist a new product with rollback protection."""
    product = Product(**product_in.model_dump())
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise


def get_product(db: Session, product_id: uuid.UUID) -> Product:
    """Retrieve a single product by primary key ID."""
    product = db.get(Product, product_id)
    if not product:
        raise NotFoundException(f"Product with id '{product_id}' not found")
    return product


def get_products(db: Session) -> List[Product]:
    """Retrieve all products."""
    statement = select(Product).order_by(Product.created_at.desc())
    return list(db.scalars(statement).all())


def delete_product(db: Session, product_id: uuid.UUID) -> None:
    """Delete a product by primary key ID with rollback protection."""
    product = get_product(db, product_id)
    db.delete(product)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
