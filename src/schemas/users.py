"""
User-related Pydantic schema module.
Defines models for user creation, update, and data representation.
"""

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    role: str


class UserSchema(BaseModel):
    """Schema for representing a user in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: str
    role: str
    is_active: bool
    is_email_verified: bool


class UserUpdate(BaseModel):
    """Schema for updating user details."""

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    role: str | None = None
    is_active: bool | None = None
    is_email_verified: bool | None = None
