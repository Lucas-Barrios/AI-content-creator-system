"""UI-agnostic FastAPI application entrypoint.

Run the backend with:
  uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""

from api_server import app

__all__ = ["app"]
