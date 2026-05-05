"""
Feedback persistence for generated content.

Current implementation: append-only JSONL files for local/demo deployments.

To be: replace FileFeedbackRepository with a Supabase-backed repository that
implements the same save() interface. The API route should not need to change;
only the repository construction should move from file storage to Supabase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Literal, Protocol
from uuid import uuid4

from src.io_helpers import append_jsonl_record

logger = logging.getLogger(__name__)

FeedbackStatus = Literal["approved", "needs_revision"]


@dataclass(frozen=True)
class FeedbackRecord:
    generation_id: str
    status: FeedbackStatus
    comment: str = ""
    request: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeedbackRepository(Protocol):
    def save(self, record: FeedbackRecord) -> FeedbackRecord:
        """Persist one feedback record."""
        ...


class FileFeedbackRepository:
    """Append feedback records to JSONL so they can later be imported to Supabase."""

    def __init__(self, path: str | Path = "feedback/generation_feedback.jsonl"):
        self.path = Path(path)

    def save(self, record: FeedbackRecord) -> FeedbackRecord:
        logger.info("Saving feedback record id=%s generation_id=%s status=%s path=%s", record.id, record.generation_id, record.status, self.path)
        append_jsonl_record(self.path, record)
        logger.info("Saved feedback record id=%s generation_id=%s", record.id, record.generation_id)
        return record


def get_feedback_repository() -> FeedbackRepository:
    """Repository factory. Swap this to SupabaseFeedbackRepository in production."""
    return FileFeedbackRepository()
