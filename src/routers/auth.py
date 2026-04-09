"""
Authentication router module.
Provides endpoints for user sign-up, sign-in, sign-out, and password management.
"""

from fastapi import APIRouter
from db.session import DBDep
from schemas.auth import UserLogin, ResetPassword, TokenRefresh, TokenRefreshResponse
from schemas.common import ResponseHandler
from schemas.users import UserCreate
from services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

auth_service = AuthService()


@router.post("/sign-up", response_model=ResponseHandler)
async def sign_up(user_data: UserCreate, db: DBDep):
    """
    Endpoint for user registration.
    """
    return await auth_service.sign_up(db, user_data)


@router.post("/sign-in")
async def sign_in(login_details: UserLogin, db: DBDep):
    """
    Endpoint for user login.
    """
    return await auth_service.sign_in(db, login_details)


@router.post("/sign-out")
async def sign_out(user_id: int, db: DBDep):
    """
    Endpoint for user sign-out.
    """
    return await auth_service.sign_out(db, user_id)


@router.post("/forgot-password")
async def forgot_password(email: str, db: DBDep):
    """
    Endpoint for requesting a password reset.
    """
    return await auth_service.forgot_password(db, email)


@router.post("/reset-password")
async def reset_password(reset_details: ResetPassword, db: DBDep):
    """
    Endpoint for resetting the password.
    """
    return await auth_service.reset_password(db, reset_details)


@router.post("/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(refresh_details: TokenRefresh, db: DBDep):
    """
    Endpoint for refreshing the access token.
    """
    return await auth_service.refresh_token(db, refresh_details)
