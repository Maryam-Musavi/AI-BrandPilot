"""
Content agent implementation.

Takes a content brief (topic + angle + keywords, and optionally
retrieval-augmented context_snippets) from ResearchAgent and drafts a
LinkedIn post in the configured brand voice, by composing the same
persona + system prompt pattern used elsewhere in the project and
delegating text generation to LLMService.

Sprint 12: when the brief includes "context_snippets" (retrieved from
the local knowledge base), they're added to the prompt as reference
material for factual grounding. This is purely additive -- when no
snippets are present (empty/not-yet-populated knowledge base), the
composed prompt is byte-for-byte identical to Sprint 11's.
"""

from typing import Any, Dict, List, Optional

from app.services.llm_service import LLMService
from app.services.persona_service import PersonaService
from app.services.prompt_service import PromptService
from memory.database import Database

SYSTEM_PROMPT_FILENAME = "system_prompt.md"


class ContentAgent:
    """Agent that drafts LinkedIn post content from a content brief."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
        persona_service: Optional[PersonaService] = None,
        database: Optional[Database] = None,
    ) -> None:
        """Initialize the agent with its collaborating services.

        Args:
            llm_service: The LLM service used to generate post text.
                Defaults to a new LLMService instance if not provided.
            prompt_service: The prompt service used to load the brand
                voice system prompt. Defaults to a new PromptService
                instance if not provided.
            persona_service: The persona service used to load brand
                persona context. Defaults to a new PersonaService
                instance if not provided.
            database: The long-term memory store used to log this
                agent's actions. Defaults to a new Database instance if
                not provided.
        """
        self.llm_service = llm_service or LLMService()
        self.prompt_service = prompt_service or PromptService()
        self.persona_service = persona_service or PersonaService()
        self.database = database or Database()

    def generate_post(self, brief: Dict[str, Any]) -> str:
        """Generate LinkedIn post content from a content brief.

        Args:
            brief: A content brief as produced by
                `ResearchAgent.create_content_brief()`, containing at
                least a "topic" key.

        Returns:
            The generated LinkedIn post text.
        """
        persona = self._load_persona_safely()
        system_prompt = self.prompt_service.load_prompt(SYSTEM_PROMPT_FILENAME)
        reference_material = self._format_context_snippets(
            brief.get("context_snippets", [])
        )
        instruction = self._build_instruction(brief)

        sections = [
            section
            for section in (persona, system_prompt, reference_material, instruction)
            if section
        ]
        combined = "\n\n".join(sections)

        content = self.llm_service.generate(combined)

        topic = brief.get("topic", "unknown")
        self.database.log_agent_action("ContentAgent", f"generated_post:{topic}")

        return content

    def _load_persona_safely(self) -> str:
        """Load the persona, tolerating a missing persona file.

        Returns:
            The formatted persona text, or an empty string if
            memory/persona.yaml does not exist.
        """
        try:
            return self.persona_service.load_persona()
        except FileNotFoundError:
            return ""

    @staticmethod
    def _format_context_snippets(snippets: List[str]) -> str:
        """Format retrieved knowledge-base snippets as reference material.

        Args:
            snippets: Chunk texts retrieved from the knowledge base for
                this brief's topic. May be empty.

        Returns:
            A formatted "Reference material" section, or an empty
            string if there are no snippets -- in which case this
            contributes nothing to the composed prompt, preserving
            Sprint 11 behavior exactly.
        """
        if not snippets:
            return ""

        lines = [
            "Reference material from the local knowledge base "
            "(for factual grounding -- use the ideas, don't quote verbatim):"
        ]
        lines.extend(f"- {snippet}" for snippet in snippets)
        return "\n".join(lines)

    @staticmethod
    def _build_instruction(brief: Dict[str, Any]) -> str:
        """Turn a content brief into a concrete writing instruction.

        Args:
            brief: The content brief, containing "topic", "angle", and
                "keywords".

        Returns:
            A plain-text instruction describing the LinkedIn post to
            write.
        """
        topic = brief.get("topic", "")
        angle = brief.get("angle", "")
        keywords = brief.get("keywords", [])

        lines = [
            "Write a single LinkedIn post in the brand voice above.",
            f"Topic: {topic}",
        ]
        if angle:
            lines.append(f"Angle: {angle}")
        if keywords:
            lines.append(f"Keywords to weave in naturally: {', '.join(keywords)}")
        lines.append(
            "Keep it concise, professional, and free of hashtags spam "
            "(at most 3 relevant hashtags at the end)."
        )

        return "\n".join(lines)
