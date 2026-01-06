"""Health check tasks for Celery."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.health.ping")
def ping() -> str:
    """Simple health check task."""
    return "pong"


@celery_app.task(name="app.tasks.health.echo")
def echo(message: str) -> str:
    """Echo task for testing."""
    return f"Echo: {message}"
