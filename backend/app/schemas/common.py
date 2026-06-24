"""Common response schemas."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Unified API response wrapper.

    All endpoints should return this structure so that frontends can handle
    successes and errors consistently.
    """

    success: bool = Field(default=True, description="Whether the request succeeded")
    message: str = Field(default="ok", description="Human-readable status message")
    data: Optional[T] = Field(default=None, description="Payload returned by the endpoint")
    error: Optional[str] = Field(default=None, description="Error message when success is False")

    def model_post_init(self, __context) -> None:
        """Ensure error is set automatically when success is False."""
        if not self.success and self.error is None:
            self.error = self.message
