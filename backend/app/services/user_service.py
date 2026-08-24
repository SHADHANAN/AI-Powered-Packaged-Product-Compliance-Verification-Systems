import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.exceptions import BadRequestException, NotFoundException


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create and persist a new user with duplicate check and rollback safety."""
    existing_user = db.scalar(select(User).where(User.email == user_in.email))
    if existing_user:
        raise BadRequestException(f"User with email '{user_in.email}' already exists")

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=f"hash_{user_in.password}",
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as exc:
        db.rollback()
        raise BadRequestException(f"User with email '{user_in.email}' already exists") from exc
    except Exception:
        db.rollback()
        raise


def get_user(db: Session, user_id: uuid.UUID) -> User:
    """Retrieve a single user by primary key ID."""
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException(f"User with id '{user_id}' not found")
    return user


def get_users(db: Session) -> List[User]:
    """Retrieve all users."""
    statement = select(User).order_by(User.created_at.desc())
    return list(db.scalars(statement).all())


def delete_user(db: Session, user_id: uuid.UUID) -> None:
    """Delete a user by primary key ID with rollback protection."""
    user = get_user(db, user_id)
    db.delete(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
