"""FastAPI application entrypoint for AI BrandPilot.

Exposes only a root and a health-check endpoint. No AI, database,
authentication, or business logic is implemented here.
"""

from fastapi import FastAPI

from app.config.settings import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


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
