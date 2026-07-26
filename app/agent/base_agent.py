"""
Abstract contract for a BrandPilot agent.

This module defines ONLY the interface that any concrete agent
implementation must follow. It contains no business logic, no AI logic,
and makes no API calls of any kind. Concrete implementations are out of
scope for this sprint.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.models.response import Response


class BaseAgent(ABC):
    """Abstract base class defining the contract for all BrandPilot agents.

    Any concrete agent (e.g. a social-media agent, a blogging agent, etc.)
    must subclass this and implement `generate_post`, `generate_article`,
    and `review`.
    """

    @abstractmethod
    async def generate_post(self, *args: Any, **kwargs: Any) -> Response:
        """Generate a short-form social media post.

        Returns:
            A Response wrapping the generated post (or an error).
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_article(self, *args: Any, **kwargs: Any) -> Response:
        """Generate a long-form article.

        Returns:
            A Response wrapping the generated article (or an error).
        """
        raise NotImplementedError

    @abstractmethod
    async def review(self, *args: Any, **kwargs: Any) -> Response:
        """Review and critique a piece of existing content.

        Returns:
            A Response wrapping the review result (or an error).
        """
        raise NotImplementedError
