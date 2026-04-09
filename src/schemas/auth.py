"""
Authentication schema module.
Defines Pydantic models for login, password reset, tokens, and related exceptions.
"""

from typing import Optional, Dict

from pydantic import BaseModel
from fastapi import status
from fastapi.exceptions import HTTPException

from schemas.users import UserSchema


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for successful login token response."""

    access_token: str
    refresh_token: str
    token_type: str
    user: UserSchema


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response."""

    access_token: str
    token_type: str = "bearer"


class ResetPassword(BaseModel):
    """Schema for password reset request."""

    email: str
    password: str
    confirm_password: str


class UserAlreadyExists(HTTPException):
    """Exception raised when a user with the same email already exists."""

    def __init__(
        self, message: str = "User already exists", details: Optional[Dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": message, "details": details},
        )


class UnauthorizedError(HTTPException):
    """Exception raised for unauthorized access."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": message, "details": details},
        )


class AccountInActive(HTTPException):
    """Exception raised when a user account is inactive."""

    def __init__(
        self, message: str = "Account Inactive", details: Optional[Dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": message, "details": details},
        )
