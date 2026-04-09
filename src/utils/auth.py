"""
Authentication utility functions for JWT token generation and validation.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM


def create_access_token(data: dict):
    """
    Creates a new JWT access token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """
    Decodes and validates a JWT access token.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def create_refresh_token(data: dict):
    """
    Creates a new JWT refresh token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt
