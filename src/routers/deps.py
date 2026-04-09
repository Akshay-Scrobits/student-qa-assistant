"""
Dependencies for FastAPI routers.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from db.session import DBDep
from models.user import User
from utils.auth import decode_access_token

security = HTTPBearer()


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security)], db: DBDep
) -> User:
    """
    Dependency to get the currently authenticated user from the JWT token.
    """
    token = auth.credentials
    payload = decode_access_token(token)
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


UserDep = Annotated[User, Depends(get_current_user)]


def role_required(allowed_roles: list[str]):
    """
    Returns a dependency that checks if the current user has one of the allowed roles.
    """

    async def role_checker(user: UserDep) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role} is not authorized to access this resource",
            )
        return user

    return role_checker
