"""
Common schema module.
Defines base models for API responses and common HTTP exceptions.
"""

from typing import Optional, Dict, Any

from pydantic import BaseModel
from fastapi import status
from fastapi.exceptions import HTTPException


class ResponseHandler(BaseModel):
    """General response handler for API responses."""

    status_code: int
    message: str
    data: Optional[Any] = None

    model_config = {"from_attributes": True}


class ClientError(HTTPException):
    """Exception raised for client-side errors (400 Bad Request)."""

    def __init__(self, message: str = "Client Error", details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": message, "details": details},
        )


class ServerError(HTTPException):
    """Exception raised for server-side errors (500 Internal Server Error)."""

    def __init__(
        self, message: str = "Internal Server Error", details: Optional[Dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": message, "details": details},
        )


class NotFoundError(HTTPException):
    """Exception raised when a resource is not found (404 Not Found)."""

    def __init__(self, message: str = "Not Found", details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": message, "details": details},
        )


class FileNotUploadedError(HTTPException):
    """Exception raised when a file upload fails."""

    def __init__(
        self, message: str = "File Not Uploaded", details: Optional[Dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": message, "details": details},
        )
