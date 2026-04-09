"""
Authentication service module.
Handles business logic for user registration, login, and token management.
"""

from fastapi import status
from sqlalchemy import select, update
from core.singletone_core import Singleton
from db.session import DBDep
from models.user import User
from schemas.users import UserCreate, UserSchema
from schemas.auth import (
    UserLogin,
    ResetPassword,
    TokenResponse,
    TokenRefresh,
    TokenRefreshResponse,
)
from schemas.common import ResponseHandler, ClientError, NotFoundError
from schemas.auth import UserAlreadyExists, UnauthorizedError, AccountInActive
from utils.auth import create_access_token, create_refresh_token, decode_access_token


class AuthService(Singleton):
    """
    Service class for authentication logic.
    Provides methods for sign-up, sign-in, sign-out, and token operations.
    """

    async def sign_up(self, db: DBDep, user_data: UserCreate) -> ResponseHandler:
        """
        This method is used to sign up a new user.
        """
        # Check if user already exists
        query = select(User).where(User.email == user_data.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise UserAlreadyExists(
                message="User with this email already exists",
                details={"email": user_data.email},
            )

        # Create new user
        new_user = User(
            email=user_data.email,
            password=user_data.password,  # Will be hashed in save_user
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            role=user_data.role,
        )

        saved_user = await User.save_user(db, new_user)
        return ResponseHandler(
            status_code=status.HTTP_201_CREATED,
            message="User created successfully",
            data=UserSchema.model_validate(saved_user),
        )

    async def sign_in(self, db: DBDep, login_details: UserLogin) -> TokenResponse:
        """
        This method is used to sign in a user.
        """
        query = select(User).where(User.email == login_details.email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError(message="Invalid email or password")

        if not User.verify_password(login_details.password, user.password):
            raise UnauthorizedError(message="Invalid email or password")

        if not user.is_active:
            raise AccountInActive(message="User account is deactivated")

        access_token = create_access_token(data={"sub": user.email})

        return TokenResponse(
            access_token=access_token,
            refresh_token=create_refresh_token(data={"sub": user.email}),
            token_type="bearer",
            user=UserSchema.model_validate(user),
        )

    async def sign_out(self, db: DBDep, user_id: int) -> ResponseHandler:
        """
        Signs out a user by nullifying their session token.
        Uses an atomic update for better performance and to avoid race conditions.
        """
        # 1. Atomic Update: Set token to None only if the user exists
        # This is faster than fetching the whole user object first
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(token=None)
            .returning(User.id)  # Ensures we know if a row was actually modified
        )

        result = await db.execute(stmt)
        updated_user_id = result.scalar_one_or_none()

        # 2. Check if the user actually existed
        if updated_user_id is None:
            raise NotFoundError(message="User not found")

        # 3. Commit the transaction
        await db.commit()

        return ResponseHandler(
            status_code=status.HTTP_200_OK, message="Successfully signed out"
        )

    async def forgot_password(self, db: DBDep, email: str):
        """
        This method is used to forgot password.
        """
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # For security reasons, don't reveal if user exists
            return {"message": "If the email exists, a reset link will be sent"}

        # Implementation of sending email would go here
        return {"message": "Reset password link sent to your email"}

    async def reset_password(self, db: DBDep, reset_details: ResetPassword):
        """
        This method is used to reset password.
        """
        if reset_details.password != reset_details.confirm_password:
            raise ClientError(message="Passwords do not match")

        query = select(User).where(User.email == reset_details.email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError()

        user.password = reset_details.password
        await User.save_user(db, user)

        return {"message": "Password reset successfully"}

    async def refresh_token(
        self, db: DBDep, refresh_details: TokenRefresh
    ) -> TokenRefreshResponse:
        """
        This method is used to refresh the access token.
        """
        payload = decode_access_token(refresh_details.refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Invalid token type")

        email = payload.get("sub")
        if not email:
            raise UnauthorizedError(message="Invalid token payload")

        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError(message="User not found")

        if not user.is_active:
            raise AccountInActive(message="User account is deactivated")

        access_token = create_access_token(data={"sub": user.email})

        return TokenRefreshResponse(access_token=access_token, token_type="bearer")
