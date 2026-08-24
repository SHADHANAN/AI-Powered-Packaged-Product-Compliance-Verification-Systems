import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import user_service

router = APIRouter(tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user account.",
)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserRead:
    return user_service.create_user(db=db, user_in=user_in)


@router.get(
    "",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List Users",
    description="Retrieve all registered users.",
)
def list_users(
    db: Session = Depends(get_db),
) -> List[UserRead]:
    return user_service.get_users(db=db)


@router.get(
    "/{id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get User",
    description="Retrieve user by unique identifier.",
)
def get_user(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> UserRead:
    return user_service.get_user(db=db, user_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete user by unique identifier.",
)
def delete_user(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    user_service.delete_user(db=db, user_id=id)
