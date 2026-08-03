"""
Base tool contract.

Defines the interface every tool in app/tools/ must implement so that
ToolRouter can dispatch to them uniformly. `execute` is the single
standardized entry point (not `run`) — this resolves the earlier
inconsistency between ToolRouter and the concrete tools.
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all tools registered with ToolRouter.

    Attributes:
        name: Short identifier for the tool.
        description: Human-readable summary of what the tool does.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Determine whether this tool can answer the given query.

        Args:
            query: The user's input text.

        Returns:
            True if this tool should handle the query, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, query: str) -> str:
        """Execute the tool against the given query.

        Args:
            query: The user's input text.

        Returns:
            The tool's result as a string.
        """
        raise NotImplementedError
