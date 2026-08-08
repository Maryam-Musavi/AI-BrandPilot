"""
Research agent implementation.

Collects candidate topics, ranks them (preferring topics that haven't
been used recently/at all, using long-term memory), and produces a
structured content brief for the content agent to write from.

Sprint 11: topic sourcing was local/mock only, behind a pluggable
`TopicSource` interface so RSS feeds, web search, LinkedIn trend data,
or company documents could be added later without changing
ResearchAgent itself.

Sprint 12 adds the first such extension -- `KnowledgeBaseTopicSource`,
which surfaces topics from locally ingested documents via
KnowledgeService -- plus optional retrieval-augmented context attached
to each content brief. Both are purely additive: `ResearchAgent()`'s own
default constructor behavior is unchanged, and `create_content_brief()`
only ever adds an extra, optional "context_snippets" key when relevant
material is actually found. With an empty/unavailable knowledge base,
behavior is identical to Sprint 11.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.services.knowledge_service import KnowledgeService
from app.memory.database import Database

_MOCK_TOPICS: List[str] = [
    "Why LLMOps is becoming its own discipline",
    "The hidden cost of running AI in the cloud vs. on-prem",
    "What private/local LLM deployment unlocks for regulated industries",
    "Prompt engineering vs. fine-tuning: when each actually pays off",
    "How agentic AI workflows change day-to-day operations",
    "Retrieval-augmented generation: hype vs. practical value",
    "Data privacy as a competitive advantage in enterprise AI",
    "Why evaluation and monitoring matter more than model choice",
    "Building AI systems that work without constant internet access",
    "What a personal AI brand manager teaches us about automation",
]


class TopicSource(ABC):
    """Interface for anything that can supply candidate topics.

    Concrete sources (RSS, web search, LinkedIn trends, company
    documents, etc.) can be added later by implementing this interface,
    without any change to ResearchAgent.
    """

    @abstractmethod
    def fetch_candidate_topics(self) -> List[str]:
        """Return a list of candidate topic strings.

        Returns:
            Candidate topics this source currently has available.
        """
        raise NotImplementedError


class LocalMockTopicSource(TopicSource):
    """Sprint 11 default topic source: a small curated local list.

    This stands in for future real sources (RSS feeds, web search,
    LinkedIn trends, company documents) while keeping the agent fully
    local, with no outbound network calls.
    """

    def __init__(self, topics: Optional[List[str]] = None) -> None:
        """Initialize the source with a fixed list of topics.

        Args:
            topics: The candidate topics to return. Defaults to a
                built-in curated list of AI/LLMOps/business topics.
        """
        self._topics = list(topics) if topics is not None else list(_MOCK_TOPICS)

    def fetch_candidate_topics(self) -> List[str]:
        """Return the configured local topic list.

        Returns:
            A copy of the configured candidate topics.
        """
        return list(self._topics)


class KnowledgeBaseTopicSource(TopicSource):
    """Derives candidate topics from ingested knowledge-base documents.

    Each ingested file becomes one candidate topic, derived from its
    filename (e.g. "why_llmops_matters.md" -> "Why Llmops Matters").
    Generated posts ("post:<id>" sources) are excluded, since they are
    prior output, not new topics to research.

    Returns an empty list -- never raises -- if the knowledge base is
    empty or the embedding backend is unavailable, so this source is
    always safe to combine with others (see `CompositeTopicSource`).
    """

    def __init__(self, knowledge_service: Optional[KnowledgeService] = None) -> None:
        """Initialize the source with a knowledge service.

        Args:
            knowledge_service: The knowledge service to read ingested
                document sources from. Defaults to a new
                KnowledgeService instance if not provided.
        """
        self.knowledge_service = knowledge_service or KnowledgeService()

    def fetch_candidate_topics(self) -> List[str]:
        """Return human-readable topics derived from ingested documents.

        Returns:
            One candidate topic per ingested (non-post) document, or an
            empty list if none are available.
        """
        try:
            sources = self.knowledge_service.list_document_sources()
        except Exception:
            return []

        topics = []
        for source in sources:
            if source.startswith("post:"):
                continue
            topics.append(_humanize_source(source))
        return topics


class CompositeTopicSource(TopicSource):
    """Combines multiple topic sources into one, concatenating results.

    Lets ResearchAgent draw candidate topics from several sources at
    once (e.g. the local mock list plus the knowledge base) without
    changing how ResearchAgent itself works.
    """

    def __init__(self, sources: List[TopicSource]) -> None:
        """Initialize with an ordered list of sources to combine.

        Args:
            sources: The topic sources to combine, in the order their
                results should be concatenated.
        """
        self.sources = sources

    def fetch_candidate_topics(self) -> List[str]:
        """Return the concatenated candidate topics from all sources.

        Returns:
            All candidate topics from every configured source, in order.
        """
        topics: List[str] = []
        for source in self.sources:
            topics.extend(source.fetch_candidate_topics())
        return topics


def _humanize_source(source: str) -> str:
    """Turn a file path/source id into a human-readable topic title.

    Args:
        source: A document source identifier (typically a file path).

    Returns:
        A title-cased, space-separated version of the file's stem, e.g.
        "knowledge/why_llmops_matters.md" -> "Why Llmops Matters".
    """
    stem = source.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return stem.replace("_", " ").replace("-", " ").title()


class ResearchAgent:
    """Agent that collects, ranks, and briefs candidate LinkedIn topics."""

    def __init__(
        self,
        topic_source: Optional[TopicSource] = None,
        database: Optional[Database] = None,
        knowledge_service: Optional[KnowledgeService] = None,
    ) -> None:
        """Initialize the agent with a topic source and long-term memory.

        Args:
            topic_source: Where candidate topics come from. Defaults to
                LocalMockTopicSource (Sprint 11 behavior, unchanged).
            database: The long-term memory store used to avoid repeating
                topics. Defaults to a new Database instance if not
                provided.
            knowledge_service: The knowledge layer used to attach
                retrieval-augmented context to content briefs. Defaults
                to a new KnowledgeService instance if not provided. Has
                no effect on behavior while the knowledge base is empty.
        """
        self.topic_source = topic_source or LocalMockTopicSource()
        self.database = database or Database()
        self.knowledge_service = knowledge_service or KnowledgeService()

    def collect_topics(self) -> List[str]:
        """Gather candidate topics from the configured topic source.

        Returns:
            The list of candidate topics currently available.
        """
        return self.topic_source.fetch_candidate_topics()

    def rank_topics(self, topics: Optional[List[str]] = None) -> List[str]:
        """Rank candidate topics, preferring less-recently-used ones.

        Topics never used before are ranked ahead of topics that have
        been used, and among used topics, the ones used least often and
        longest ago are ranked first.

        Args:
            topics: The candidate topics to rank. Defaults to the result
                of `collect_topics()` if not provided.

        Returns:
            The topics sorted from most to least preferred.
        """
        candidates = topics if topics is not None else self.collect_topics()

        def sort_key(topic: str) -> tuple:
            usage = self.database.get_topic_usage(topic)
            if usage is None:
                return (0, "")
            return (usage["used_count"], usage["last_used"] or "")

        return sorted(candidates, key=sort_key)

    def create_content_brief(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Produce a structured content brief for the content agent.

        Args:
            topic: A specific topic to brief on. If not provided, the
                top-ranked candidate topic is chosen automatically.

        Returns:
            A dict with the chosen topic, a suggested angle, and
            keywords, e.g.:
            {"topic": "...", "angle": "...", "keywords": ["..."]}.
        """
        if topic is not None:
            chosen_topic = topic
        else:
            ranked = self.rank_topics()
            chosen_topic = ranked[0] if ranked else "AI and LLMOps trends"

        brief: Dict[str, Any] = {
            "topic": chosen_topic,
            "angle": (
                f"Share a clear, professional perspective on '{chosen_topic}' "
                "that gives the audience one practical takeaway."
            ),
            "keywords": [chosen_topic],
        }

        context_snippets = self._retrieve_context_safely(chosen_topic)
        if context_snippets:
            brief["context_snippets"] = context_snippets

        self.database.log_agent_action(
            "ResearchAgent", f"created_content_brief:{chosen_topic}"
        )
        return brief

    def _retrieve_context_safely(self, topic: str) -> List[str]:
        """Retrieve knowledge-base context for a topic, tolerating failure.

        Args:
            topic: The topic to retrieve supporting context for.

        Returns:
            Up to a few relevant chunk texts, or an empty list if the
            knowledge base is empty, unavailable, or retrieval fails for
            any other reason.
        """
        try:
            return self.knowledge_service.retrieve(topic, top_k=3)
        except Exception:
            return []
