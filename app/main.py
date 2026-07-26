"""FastAPI application entrypoint for AI BrandPilot.

Exposes a root endpoint, a health-check endpoint, and a mock chat
endpoint. No real AI, database, authentication, or business logic is
implemented here.
"""

from fastapi import FastAPI

from app.agent.base_agent import BaseAgent
from app.config.settings import settings
from app.models.message import ChatRequest
from app.models.response import ChatResponse

app = FastAPI(title=settings.app_name, version="0.1.0")
agent = BaseAgent()


@app.get("/")
async def root() -> dict[str, str]:
    """Return a simple welcome message identifying the API.

    Returns:
        A dict containing a static welcome message.
    """
    return {"message": "AI BrandPilot API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Report the liveness status of the API.

    Returns:
        A dict indicating the service is up and running.
    """
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle a chat request via BaseAgent -> LLMService -> mock response.

    Args:
        request: The incoming chat request containing the user's message.

    Returns:
        A ChatResponse wrapping the (mock) generated response.
    """
    result = agent.chat(request.message)
    return ChatResponse(response=result)
