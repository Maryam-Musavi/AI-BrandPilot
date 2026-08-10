"""
Persona management service.

Loads the persona definition from memory/persona.yaml and formats it into
a plain, human-readable text block. No AI logic, no business logic, and
no API calls are implemented here.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

PERSONA_PATH = (
    Path(__file__).resolve().parent.parent / "memory" / "persona.yaml"
)

_FIELDS: List[tuple[str, str]] = [
    ("Name", "name"),
    ("Headline", "headline"),
    ("Background", "background"),
    ("Skills", "skills"),
    ("Goals", "goals"),
    ("Audience", "audience"),
    ("Tone", "tone"),
    ("Languages", "languages"),
    ("Values", "values"),
]


class PersonaService:
    """Loads and formats the persona defined in memory/persona.yaml."""

    def __init__(self, persona_path: Optional[Path] = None) -> None:
        """Initialize the service with a persona file path.

        Args:
            persona_path: Path to the persona YAML file. Defaults to
                memory/persona.yaml.
        """
        self._persona_path = persona_path or PERSONA_PATH

    def load_persona(self) -> str:
        """Load persona.yaml and return a formatted text block.

        Returns:
            A human-readable, formatted representation of the persona.

        Raises:
            FileNotFoundError: If memory/persona.yaml does not exist.
        """
        if not self._persona_path.is_file():
            raise FileNotFoundError(
                f"Persona file not found: {self._persona_path}"
            )

        with self._persona_path.open("r", encoding="utf-8") as file:
            data: Dict[str, Any] = yaml.safe_load(file) or {}

        return self._format_persona(data)

    @staticmethod
    def _format_persona(data: Dict[str, Any]) -> str:
        """Format raw persona data into the standard text block layout.

        Args:
            data: Parsed persona YAML data.

        Returns:
            The formatted "Label:\\nvalue" text block for all fields.
        """

        def stringify(value: Union[str, List[Any], None]) -> str:
            if value is None:
                return ""
            if isinstance(value, list):
                return ", ".join(str(item) for item in value)
            return str(value).strip()

        lines: List[str] = []
        for label, key in _FIELDS:
            lines.append(f"{label}:")
            lines.append(stringify(data.get(key)))
            lines.append("")

        return "\n".join(lines).strip()
