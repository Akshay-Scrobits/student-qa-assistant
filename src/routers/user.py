"""
User router module.
Provides endpoints for updating and deleting user details.
"""

from fastapi import APIRouter
from db.session import DBDep
from services.user import UserService
from schemas.users import UserUpdate
from schemas.common import ResponseHandler
from routers.deps import UserDep

router = APIRouter(prefix="/users", tags=["Users"])

user_service = UserService()


@router.put("/{user_id}", response_model=ResponseHandler)
async def update_user(
    user_id: int, update_data: UserUpdate, db: DBDep, _current_user: UserDep
):
    """
    Endpoint to update user details.
    """
    return await user_service.update_user(db, user_id, update_data)


@router.delete("/{user_id}", response_model=ResponseHandler)
async def delete_user(user_id: int, db: DBDep, _current_user: UserDep):
    """
    Endpoint to delete a user.
    """
    return await user_service.delete_user(db, user_id)
