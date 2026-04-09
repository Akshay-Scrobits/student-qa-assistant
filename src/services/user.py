"""
User service module.
Handles business logic for user profile updates and deletion.
"""

from sqlalchemy import select
from fastapi import status

from db.session import DBDep
from models.user import User
from schemas.users import UserUpdate, UserSchema
from schemas.common import ResponseHandler, NotFoundError
from core.singletone_core import Singleton


class UserService(Singleton):
    """
    Service class for user management.
    Provides methods for updating and deleting user records.
    """

    async def update_user(
        self, db: DBDep, user_id: int, update_data: UserUpdate
    ) -> ResponseHandler:
        """
        Update a user's details.
        """
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(message="User not found")

        # Update fields if provided
        data = update_data.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        user_schema = UserSchema.model_validate(user)
        return ResponseHandler(
            status_code=status.HTTP_200_OK,
            message="User updated successfully",
            data=user_schema,
        )

    async def delete_user(self, db: DBDep, user_id: int) -> ResponseHandler:
        """
        Delete a user from the database.
        """
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(message="User not found")

        await db.delete(user)
        await db.commit()

        return ResponseHandler(
            status_code=status.HTTP_200_OK, message="User deleted successfully"
        )
