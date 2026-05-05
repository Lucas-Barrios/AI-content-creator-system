"""Central logging configuration for backend debugging and monitoring."""

from __future__ import annotations

import logging
from pathlib import Path

LOG_PATH = Path("logs/ai_content_creator.log")


def configure_logging(level: int = logging.INFO, log_path: Path = LOG_PATH) -> None:
    """Configure application logging once for file and console output."""
    log_path.parent.mkdir(exist_ok=True)
    root_logger = logging.getLogger()

    if any(getattr(handler, "_ai_content_creator_handler", False) for handler in root_logger.handlers):
        return

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    file_handler._ai_content_creator_handler = True  # type: ignore[attr-defined]

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler._ai_content_creator_handler = True  # type: ignore[attr-defined]

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
