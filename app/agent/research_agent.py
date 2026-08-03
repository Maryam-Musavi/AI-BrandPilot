"""
Research agent implementation.

Collects candidate topics, ranks them (preferring topics that haven't
been used recently/at all, using long-term memory), and produces a
structured content brief for the content agent to write from.

Sprint 11 scope: topic sourcing is local/mock only (no external API
calls), but behind a pluggable `TopicSource` interface so RSS feeds, web
search, LinkedIn trend data, or company documents can be added later
without changing ResearchAgent itself.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from memory.database import Database

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


class ResearchAgent:
    """Agent that collects, ranks, and briefs candidate LinkedIn topics."""

    def __init__(
        self,
        topic_source: Optional[TopicSource] = None,
        database: Optional[Database] = None,
    ) -> None:
        """Initialize the agent with a topic source and long-term memory.

        Args:
            topic_source: Where candidate topics come from. Defaults to
                LocalMockTopicSource (Sprint 11 scope: local/mock only).
            database: The long-term memory store used to avoid repeating
                topics. Defaults to a new Database instance if not
                provided.
        """
        self.topic_source = topic_source or LocalMockTopicSource()
        self.database = database or Database()

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

        self.database.log_agent_action(
            "ResearchAgent", f"created_content_brief:{chosen_topic}"
        )
        return brief
