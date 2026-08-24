import uuid
from typing import Callable, List, Optional
from fastapi import Depends

from app.api.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User
from app.models.verification import Verification
from app.utils.exceptions import ForbiddenException


def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure that the caller has a valid, active authenticated session."""
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing role-based access control."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Insufficient permissions: required one of {[r.value for r in allowed_roles]}, "
                f"current role '{current_user.role.value}'"
            )
        return current_user

    return role_checker


# Role-specific shortcut dependencies
require_admin = require_roles(UserRole.ADMIN)
require_inspector = require_roles(UserRole.ADMIN, UserRole.INSPECTOR)
require_viewer = require_roles(UserRole.ADMIN, UserRole.INSPECTOR, UserRole.VIEWER)


def verify_verification_ownership(verification: Verification, user: User) -> None:
    """Validate resource ownership for verifications and associated reports/audit logs."""
    # ADMIN users have full system-wide oversight
    if user.role == UserRole.ADMIN:
        return

    # INSPECTOR users can access verifications assigned to them or unassigned
    if user.role == UserRole.INSPECTOR:
        if verification.inspector_id is not None and verification.inspector_id != user.id:
            raise ForbiddenException("Access denied: verification belongs to another inspector")
        return

    # VIEWER users can inspect assigned verifications
    if user.role == UserRole.VIEWER:
        if verification.inspector_id is not None and verification.inspector_id != user.id:
            raise ForbiddenException("Access denied: you do not have permission to access this verification")
        return

    raise ForbiddenException("Access denied: insufficient privileges")


def verify_user_profile_ownership(target_user_id: uuid.UUID, current_user: User) -> None:
    """Ensure a user can only access/modify their own account, unless they are an ADMIN."""
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.id != target_user_id:
        raise ForbiddenException("Access denied: cannot access or modify another user's account")
