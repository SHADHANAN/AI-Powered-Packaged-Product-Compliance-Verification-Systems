from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate with email and password to receive a JWT Bearer access token.",
)
def login(
    login_in: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth_service.authenticate_user(
        db=db,
        email=login_in.email,
        password=login_in.password,
    )
    access_token = auth_service.create_access_token_for_user(user)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Current User Profile",
    description="Retrieve the profile of the currently authenticated user from the Bearer token.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return current_user
