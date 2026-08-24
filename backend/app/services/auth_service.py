from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.exceptions import UnauthorizedException
from app.utils.logging import get_logger
from app.utils.security import create_access_token, verify_password

logger = get_logger("app.services.auth")


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate user credentials safely.
    
    Verifies user existence, Argon2 password hash, and active status.
    Raises UnauthorizedException with generic message on failure without leaking details.
    """
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        logger.info(f"Authentication failed: email '{email}' not found")
        raise UnauthorizedException("Incorrect email or password")

    if not verify_password(password, user.password_hash):
        logger.info(f"Authentication failed: invalid password for user '{user.id}'")
        raise UnauthorizedException("Incorrect email or password")

    if not user.is_active:
        logger.info(f"Authentication failed: user account '{user.id}' is inactive")
        raise UnauthorizedException("Incorrect email or password")

    return user


def create_access_token_for_user(user: User) -> str:
    """Generate a signed JWT access token for an authenticated user."""
    return create_access_token(user_id=user.id, role=user.role.value)
