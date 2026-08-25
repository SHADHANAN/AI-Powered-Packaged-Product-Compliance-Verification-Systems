import uuid
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.exceptions import UnauthorizedException
from app.utils.logging import get_logger
from app.utils.security import decode_access_token

logger = get_logger("app.dependencies")
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract, decode, and validate the Bearer JWT token to return the authenticated User."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(
            "Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException(
            "Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(
            "Malformed authentication token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(
            "Malformed authentication token: invalid subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedException(
            "User account associated with this token does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise UnauthorizedException(
            "User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
