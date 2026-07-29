"""
Prompt management service.

Provides a simple contract for loading prompt template files from disk
(app/prompts/). No AI logic, no business logic, and no API calls are
implemented here.
"""

from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptService:
    """Loads prompt files from the app/prompts/ directory."""

    def __init__(self, prompts_dir: Optional[Path] = None) -> None:
        """Initialize the service with a prompts directory.

        Args:
            prompts_dir: Directory containing prompt files. Defaults to
                app/prompts/.
        """
        self._prompts_dir = prompts_dir or PROMPTS_DIR

    def load_prompt(self, filename: str) -> str:
        """Load and return the contents of a prompt file.

        Args:
            filename: Name of the prompt file (e.g. "system_prompt.md").

        Returns:
            The file's text content, stripped of surrounding whitespace.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        path = self._prompts_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
