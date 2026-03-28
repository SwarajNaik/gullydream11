"""Common API response schemas."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    message: str = ""
    data: Optional[T] = None


class SuccessResponse(BaseModel):
    """Simple success response without data."""

    success: bool = True
    message: str = ""


def success_response(message: str = "Success", data: any = None) -> dict:
    """Helper to create a success response dict."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str = "Error") -> dict:
    """Helper to create an error response dict."""
    return {"success": False, "message": message, "data": None}
