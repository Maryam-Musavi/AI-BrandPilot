"""
Core data contract for a standardized application response envelope.

This module defines ONLY the data shape used to wrap results returned by
services and agents throughout the application. It contains no business
logic, no AI logic, and no API calls.
"""

from typing import Any, Optional

from pydantic import BaseModel


class Response(BaseModel):
    """Generic response envelope returned by services and agents.

    Attributes:
        success: Whether the operation completed successfully.
        message: A human-readable message describing the result or error.
        data: Optional payload containing the result of the operation.
            The shape of this payload is intentionally left generic and is
            defined by whichever caller populates it.
    """

    success: bool
    message: str
    data: Optional[Any] = None
