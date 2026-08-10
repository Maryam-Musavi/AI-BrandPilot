"""Regression tests guarding against import/wiring bugs.

These modules previously used `from memory.xxx import ...` (missing the
`app.` prefix), which made them impossible to import at all --
`LinkedInAgent`, `ContentAgent`, `ResearchAgent`, and `KnowledgeService`
all raised `ModuleNotFoundError` as soon as anything touched them,
which meant the entire LinkedIn workflow (the actual point of this
project) silently could never run. This test simply ensures every
agent/service module still imports cleanly.
"""

import importlib

import pytest

MODULES = [
    "app.main",
    "app.agent.base_agent",
    "app.agent.content_agent",
    "app.agent.research_agent",
    "app.agent.linkedin_agent",
    "app.services.knowledge_service",
    "app.services.llm_service",
    "app.services.persona_service",
    "app.services.prompt_service",
    "app.memory.database",
    "app.memory.knowledge_store",
    "app.memory.conversation_memory",
    "app.tools.tool_router",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports_cleanly(module_name: str) -> None:
    """Every production module must import without raising."""
    importlib.import_module(module_name)
