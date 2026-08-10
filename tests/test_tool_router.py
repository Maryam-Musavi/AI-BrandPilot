"""Tests for app/tools/tool_router.py and its registered tools."""

from app.tools.tool_router import ToolRouter


def test_calculator_query_is_routed_and_evaluated() -> None:
    router = ToolRouter()
    result = router.route("what is 8*5?")

    assert result is not None
    assert "40" in result


def test_datetime_query_is_routed() -> None:
    router = ToolRouter()
    result = router.route("what time is it?")

    assert result is not None
    assert "time" in result.lower()


def test_unrelated_query_is_not_routed() -> None:
    router = ToolRouter()
    result = router.route("tell me about LLMOps")

    assert result is None
