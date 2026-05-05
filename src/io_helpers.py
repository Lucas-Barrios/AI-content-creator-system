"""Small file/JSON helpers shared by backend modules."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json_file(file_path: str | Path) -> dict[str, Any]:
    """Load and parse a JSON object from disk."""
    path = Path(file_path)
    logger.info("Loading JSON file from %s", path)
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as error:
        logger.error("Failed to load JSON file, missing path=%s", path)
        raise FileNotFoundError(
            f"JSON file not found: {path}\n"
            "  Suggestion: check the file path and make sure the file exists."
        ) from error
    except json.JSONDecodeError as error:
        logger.error("Invalid JSON in %s at line=%s column=%s: %s", path, error.lineno, error.colno, error.msg)
        raise ValueError(
            f"Invalid JSON in {path} at line {error.lineno}, column {error.colno}: {error.msg}\n"
            "  Suggestion: fix the JSON syntax at the reported line and column."
        ) from error
    if not isinstance(data, dict):
        logger.error("Invalid JSON data shape in %s: expected object got %s", path, type(data).__name__)
        raise ValueError(
            f"Expected JSON object in {path}, got {type(data).__name__}\n"
            "  Suggestion: use a top-level JSON object such as {\"key\": \"value\"}."
        )
    logger.info("Loaded JSON file successfully from %s", path)
    return data


def append_jsonl_record(file_path: str | Path, record: Any) -> None:
    """Append one JSON-serializable record to a JSONL file."""
    path = Path(file_path)
    path.parent.mkdir(exist_ok=True)
    logger.info("Appending JSONL record to %s", path)

    if is_dataclass(record) and not isinstance(record, type):
        payload = asdict(record)
    else:
        payload = record

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    logger.info("Appended JSONL record to %s", path)


def read_text_without_metadata(file_path: str | Path, metadata_prefix: str = "<!--") -> str:
    """Read text and remove metadata/comment lines with the configured prefix."""
    path = Path(file_path)
    logger.info("Reading text file from %s", path)
    raw = path.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if not line.strip().startswith(metadata_prefix)]
    content = "\n".join(lines).strip()
    logger.info("Read text file from %s chars=%s", path, len(content))
    return content
