import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.product import ProductCreate, ProductRead
from app.services import product_service

router = APIRouter(tags=["Products"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product",
    description="Create a new packaged commodity entry.",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
) -> ProductRead:
    return product_service.create_product(db=db, product_in=product_in)


@router.get(
    "",
    response_model=List[ProductRead],
    status_code=status.HTTP_200_OK,
    summary="List Products",
    description="Retrieve all packaged product commodities.",
)
def list_products(
    db: Session = Depends(get_db),
) -> List[ProductRead]:
    return product_service.get_products(db=db)


@router.get(
    "/{id}",
    response_model=ProductRead,
    status_code=status.HTTP_200_OK,
    summary="Get Product",
    description="Retrieve a product commodity by unique identifier.",
)
def get_product(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProductRead:
    return product_service.get_product(db=db, product_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Product",
    description="Delete a product commodity by unique identifier.",
)
def delete_product(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    product_service.delete_product(db=db, product_id=id)
