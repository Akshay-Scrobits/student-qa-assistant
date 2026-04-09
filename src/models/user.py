"""
User model module.
Defines the User SQLAlchemy model and related methods for password hashing and verification.
"""

import bcrypt

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession

from models.base import Base


class User(AsyncAttrs, Base):
    """
    SQLAlchemy model representing a user.
    """

    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    phone_number: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    def __str__(self):
        return self.email

    @staticmethod
    async def save_user(db: AsyncSession, user: "User"):
        """
        This method is used to hash the password and saving the user.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), salt)
        user.password = hashed_password.decode("utf-8")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        This method is used to verify the password.
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
