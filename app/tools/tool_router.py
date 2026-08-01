"""
Tool router implementation.

Owns all available tools and routes a query to the first registered
tool that reports it can handle it. No AI logic, external API calls, or
persistence is implemented here.
"""

from typing import List, Optional

from app.tools.base_tool import BaseTool
from app.tools.calculator_tool import CalculatorTool
from app.tools.datetime_tool import DateTimeTool


class ToolRouter:
    """Routes a query to the first registered tool that can handle it.

    Attributes:
        tools: The ordered list of registered tools.
    """

    def __init__(self, tools: Optional[List[BaseTool]] = None) -> None:
        """Initialize the router with its registered tools.

        Args:
            tools: The tools to register, checked in order. Defaults to
                the standard set (DateTimeTool, CalculatorTool) if not
                provided.
        """
        self.tools: List[BaseTool] = (
            tools if tools is not None else [DateTimeTool(), CalculatorTool()]
        )

    def route(self, query: str) -> Optional[str]:
        """Route a query to the first tool able to handle it.

        Args:
            query: The user's input text.

        Returns:
            The result string from the first matching tool, or None if
            no registered tool can handle the query.
        """
        for tool in self.tools:
            if tool.can_handle(query):
                return tool.execute(query)
        return None
