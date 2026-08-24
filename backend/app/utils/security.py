import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("app.security")
settings = get_settings()

# Initialize PasswordHash using Argon2 algorithm
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Securely hash a plaintext password using Argon2id with unique salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Safely verify a plaintext password against an Argon2 password hash.
    
    Returns False on invalid input, mismatch, or corrupted hash without crashing.
    """
    if not password or not password_hash:
        return False
    try:
        return _password_hash.verify(password, password_hash)
    except Exception as exc:
        logger.warning(f"Password verification encountered an invalid/corrupted hash: {exc}")
        return False


def create_access_token(
    user_id: Union[uuid.UUID, str],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token containing subject, role, and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": str(role),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Safely decode and validate a JWT access token.
    
    Returns payload dictionary if valid, or None if invalid, expired, or tampered.
    """
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
        return payload
    except jwt.PyJWTError as exc:
        logger.debug(f"JWT token decoding/validation rejected: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"Unexpected error while decoding JWT: {exc}")
        return None
