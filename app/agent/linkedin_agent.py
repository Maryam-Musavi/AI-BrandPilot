"""
LinkedIn agent implementation.

Orchestrates the end-to-end LinkedIn content workflow:

    ResearchAgent -> ContentAgent -> LinkedInAgent -> draft saved to
    the database -> human approval required.

Sprint 11 scope: NO automatic publishing. This agent only ever produces
drafts and stores them with a "pending_approval" (or "idea") status.
Publishing to LinkedIn is out of scope until OAuth/credentials/approval
workflow are addressed in a future sprint.

Sprint 12 adds the knowledge layer:
- ResearchAgent's default topic source now combines the local mock list
  with topics derived from the knowledge base (empty knowledge base ->
  identical behavior to Sprint 11).
- After a draft is generated and saved to business memory
  (memory/database.py), its content is also embedded and stored in the
  knowledge base (memory/knowledge_store.py), so future retrieval
  includes what's already been said. This step is best-effort: if the
  embedding backend is unavailable, it's logged and skipped -- it never
  blocks or breaks the primary posting workflow.
"""

from typing import Any, Dict, Optional

from app.agent.content_agent import ContentAgent
from app.agent.research_agent import (
    CompositeTopicSource,
    KnowledgeBaseTopicSource,
    LocalMockTopicSource,
    ResearchAgent,
)
from app.services.knowledge_service import KnowledgeService
from memory.database import Database

STATUS_IDEA = "idea"
STATUS_PENDING_APPROVAL = "pending_approval"


class LinkedInAgent:
    """Agent that orchestrates the research -> content -> draft workflow."""

    def __init__(
        self,
        research_agent: Optional[ResearchAgent] = None,
        content_agent: Optional[ContentAgent] = None,
        database: Optional[Database] = None,
        knowledge_service: Optional[KnowledgeService] = None,
    ) -> None:
        """Initialize the agent and its collaborators.

        A single shared Database instance is used by default so that
        ResearchAgent, ContentAgent, and LinkedInAgent all read/write the
        same long-term (business) memory. Likewise, a single shared
        KnowledgeService is used for the (separate) knowledge memory.

        Args:
            research_agent: The research agent to use. Defaults to a new
                ResearchAgent whose topic source combines the local
                mock list with knowledge-base-derived topics, sharing
                this agent's database and knowledge service.
            content_agent: The content agent to use. Defaults to a new
                ContentAgent sharing this agent's database.
            database: The business long-term memory store. Defaults to
                a new Database instance if not provided.
            knowledge_service: The knowledge layer (RAG) service.
                Defaults to a new KnowledgeService instance if not
                provided. Has no effect on the workflow's core behavior
                while the knowledge base is empty.
        """
        self.database = database or Database()
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.research_agent = research_agent or ResearchAgent(
            topic_source=CompositeTopicSource(
                [
                    LocalMockTopicSource(),
                    KnowledgeBaseTopicSource(self.knowledge_service),
                ]
            ),
            database=self.database,
            knowledge_service=self.knowledge_service,
        )
        self.content_agent = content_agent or ContentAgent(database=self.database)

    def generate_post_idea(self) -> Dict[str, Any]:
        """Run the "idea" step of the workflow (e.g. the Monday task).

        Researches and selects a topic, then saves it as an idea (no
        content yet) so it can be drafted later.

        Returns:
            A dict with the new post's id and the content brief used,
            e.g. {"post_id": 1, "brief": {...}}.
        """
        brief = self.research_agent.create_content_brief()

        post_id = self.database.create_post(
            topic=brief["topic"], content="", status=STATUS_IDEA
        )
        self.research_agent.database.record_topic_used(brief["topic"])

        self.database.log_agent_action(
            "LinkedInAgent", f"generated_post_idea:{brief['topic']}"
        )

        return {"post_id": post_id, "brief": brief}

    def generate_post_draft(self, post_id: Optional[int] = None) -> Dict[str, Any]:
        """Run the "draft" step of the workflow (e.g. the Wednesday task).

        If `post_id` refers to an existing idea, that post's topic is
        drafted and updated in place. Otherwise, a fresh topic is
        researched and a brand-new post record is created. Either way,
        the result is saved with status "pending_approval" -- no
        publishing happens automatically.

        Args:
            post_id: The id of an existing idea to draft, if any.

        Returns:
            A dict describing the saved draft, e.g.
            {"post_id": 1, "topic": "...", "content": "...",
             "status": "pending_approval"}.
        """
        existing_post = self.database.get_post(post_id) if post_id is not None else None
        topic = existing_post["topic"] if existing_post else None

        brief = self.research_agent.create_content_brief(topic=topic)
        content = self.content_agent.generate_post(brief)

        if existing_post is not None:
            self.database.update_post_content(
                post_id, content=content, status=STATUS_PENDING_APPROVAL
            )
            saved_post_id = existing_post["id"]
        else:
            saved_post_id = self.database.create_post(
                topic=brief["topic"], content=content, status=STATUS_PENDING_APPROVAL
            )
            self.research_agent.database.record_topic_used(brief["topic"])

        self.database.log_agent_action(
            "LinkedInAgent", f"generated_post_draft:{brief['topic']}"
        )

        self._ingest_post_into_knowledge_base(saved_post_id, content)

        return {
            "post_id": saved_post_id,
            "topic": brief["topic"],
            "content": content,
            "status": STATUS_PENDING_APPROVAL,
        }

    def _ingest_post_into_knowledge_base(self, post_id: int, content: str) -> None:
        """Embed a generated post into the knowledge base, best-effort.

        Per the Sprint 12 workflow: draft generated -> saved into
        business memory (already done by the caller) -> embedded ->
        stored in the knowledge base. This step never blocks or breaks
        the primary posting workflow: if it fails (e.g. the embedding
        backend is unavailable), the failure is logged to business
        memory and swallowed.

        Args:
            post_id: The id of the post that was just saved.
            content: The post's text content.
        """
        try:
            self.knowledge_service.ingest_generated_post(post_id, content)
        except Exception:
            self.database.log_agent_action(
                "LinkedInAgent", f"knowledge_ingestion_failed:post:{post_id}"
            )
