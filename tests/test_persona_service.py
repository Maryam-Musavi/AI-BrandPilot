"""Tests for app/services/persona_service.py.

Regression coverage for a path bug: PERSONA_PATH previously resolved to
<repo_root>/memory/persona.yaml instead of <repo_root>/app/memory/persona.yaml,
so the real file was never found. BaseAgent/ContentAgent both swallow the
resulting FileNotFoundError, so the bug was invisible -- the brand
persona was silently never injected into any prompt.
"""

from app.services.persona_service import PersonaService


def test_default_persona_path_points_inside_app_memory() -> None:
    service = PersonaService()

    assert service._persona_path.parent.name == "memory"
    assert service._persona_path.parent.parent.name == "app"
    assert service._persona_path.is_file(), (
        f"Expected persona.yaml at {service._persona_path}"
    )


def test_load_persona_returns_non_empty_text() -> None:
    service = PersonaService()
    persona_text = service.load_persona()

    assert isinstance(persona_text, str)
    assert persona_text.strip() != ""
