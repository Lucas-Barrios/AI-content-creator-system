"""
repurpose_service.py

Content Repurposing Engine — orchestrates the two-stage AI pipeline and persists
every result to Supabase using the existing generated_outputs + parent_output_id
lineage pattern.

Flow:
  1. Validate inputs
  2. Extract meaning from source text  → ContentExtraction (JSON)
  3. (optional) Retrieve brand context → brand_block
  4. For each target format            → generate_format_asset() → RepurposedOutput
  5. Persist source entry              → generated_outputs (parent_output_id = NULL)
  6. Persist each output               → generated_outputs (parent_output_id = source_id)
  7. Return RepurposeResult

Single-asset regeneration (regenerate_output) re-runs stage 4 for one format
and updates the existing generated_output row in-place.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from dotenv import load_dotenv

from src.brand_intelligence import assemble_brand_block, retrieve_brand_context
from src.llm_integration import ContentGenerator, ContentGeneratorError
from src.repurpose_prompt_templates import (
    FORMAT_META,
    VALID_FORMATS,
    extract_prompt,
    format_prompt,
)
from src.supabase_client import get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)

VALID_SOURCE_TYPES = {
    "blog_post", "transcript", "webinar_notes", "article",
    "social_post", "document", "other",
}


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class RepurposeRequest:
    organization_id: str
    client_id: str
    project_id: str
    source_text: str
    source_title: str
    source_type: str = "article"
    target_formats: list[str] = field(default_factory=list)
    language: str = "english"
    preserve_tone: bool = True       # if False, use brand tone instead of source tone
    brand_profile_id: str | None = None
    created_by: str | None = None


@dataclass
class ContentExtraction:
    title: str
    core_argument: str
    key_points: list[str]
    facts: list[str]
    quotes: list[str]
    tone: str
    audience_signals: str
    one_sentence_summary: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepurposedOutput:
    output_id: str
    format: str
    label: str
    content_type: str
    channel: str
    content: str
    word_count: int
    status: str = "draft"


@dataclass
class RepurposeResult:
    source_id: str
    extraction: ContentExtraction
    outputs: list[RepurposedOutput]
    created_at: str


# ── Validation ─────────────────────────────────────────────────────────────────

def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID.") from exc
    return value


def validate_request(req: RepurposeRequest) -> None:
    _validate_uuid(req.organization_id, "organization_id")
    _validate_uuid(req.client_id, "client_id")
    _validate_uuid(req.project_id, "project_id")
    if req.brand_profile_id:
        _validate_uuid(req.brand_profile_id, "brand_profile_id")
    if not req.source_text.strip():
        raise ValueError("source_text is required.")
    if len(req.source_text.strip()) < 50:
        raise ValueError("source_text must be at least 50 characters.")
    if not req.target_formats:
        raise ValueError("At least one target format must be selected.")
    bad = set(req.target_formats) - VALID_FORMATS
    if bad:
        raise ValueError(f"Unknown formats: {bad}. Valid: {sorted(VALID_FORMATS)}")


# ── Stage 1: Extraction ────────────────────────────────────────────────────────

def _parse_extraction(raw_json: str) -> ContentExtraction:
    try:
        data = json.loads(raw_json.strip())
    except json.JSONDecodeError:
        stripped = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(stripped)

    return ContentExtraction(
        title=str(data.get("title") or ""),
        core_argument=str(data.get("core_argument") or ""),
        key_points=list(data.get("key_points") or []),
        facts=list(data.get("facts") or []),
        quotes=list(data.get("quotes") or []),
        tone=str(data.get("tone") or ""),
        audience_signals=str(data.get("audience_signals") or ""),
        one_sentence_summary=str(data.get("one_sentence_summary") or ""),
        raw=data,
    )


def extract_meaning(
    source_text: str,
    source_type: str,
    generator: ContentGenerator,
) -> ContentExtraction:
    logger.info("Extracting meaning source_type=%s source_chars=%s", source_type, len(source_text))
    prompt = extract_prompt(source_text, source_type)
    raw = generator.generate_content(prompt)
    extraction = _parse_extraction(raw)
    logger.info(
        "Extraction complete title='%s' key_points=%s facts=%s",
        extraction.title, len(extraction.key_points), len(extraction.facts),
    )
    return extraction


# ── Stage 2: Per-format adaptation ────────────────────────────────────────────

def adapt_for_format(
    fmt: str,
    extraction: ContentExtraction,
    brand_block: str,
    language: str,
    generator: ContentGenerator,
) -> str:
    logger.info("Adapting content format=%s", fmt)
    prompt = format_prompt(fmt, extraction.raw, brand_block, language)
    content = generator.generate_content(prompt)
    logger.info("Format adaptation complete format=%s chars=%s", fmt, len(content))
    return content


# ── Supabase persistence ───────────────────────────────────────────────────────

class RepurposeRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.db = client or get_supabase_admin_client()

    def _base_output_payload(
        self,
        req: RepurposeRequest,
        title: str,
        content: str,
        content_type: str,
        channel: str,
        metadata: dict,
    ) -> dict:
        return {
            "organization_id": req.organization_id,
            "client_id": req.client_id,
            "project_id": req.project_id,
            "title": title,
            "content": content,
            "content_type": content_type,
            "channel": channel if channel in {
                "website", "linkedin", "instagram", "facebook", "x",
                "email", "newsletter", "ads", "blog", "other",
            } else "other",
            "language": req.language,
            "status": "draft",
            "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
            "word_count": len(content.split()),
            "metadata": metadata,
            "created_by": req.created_by,
        }

    def save_source(self, req: RepurposeRequest, extraction: ContentExtraction) -> tuple[str, str]:
        """Persist the source text as a generated_output. Returns (source_id, created_at)."""
        payload = self._base_output_payload(
            req,
            title=f"[SOURCE] {extraction.title or req.source_title}",
            content=req.source_text,
            content_type="other",
            channel="other",
            metadata={
                "is_repurpose_source": True,
                "source_type": req.source_type,
                "source_title": req.source_title,
                "extraction": extraction.raw,
                "target_formats": req.target_formats,
            },
        )
        response = self.db.table("generated_outputs").insert(payload).execute()
        row = response.data[0]
        return str(row["id"]), str(row["created_at"])

    def save_output(
        self,
        req: RepurposeRequest,
        source_id: str,
        fmt: str,
        content: str,
    ) -> str:
        meta = FORMAT_META[fmt]
        payload = self._base_output_payload(
            req,
            title=meta["label"],
            content=content,
            content_type=meta["content_type"],
            channel=meta["channel"],
            metadata={"repurpose_format": fmt, "source_output_id": source_id},
        )
        payload["parent_output_id"] = source_id
        response = self.db.table("generated_outputs").insert(payload).execute()
        return str(response.data[0]["id"])

    def update_output(self, output_id: str, content: str) -> None:
        self.db.table("generated_outputs").update({
            "content": content,
            "word_count": len(content.split()),
            "status": "draft",
        }).eq("id", output_id).execute()

    def get_source_with_outputs(self, source_id: str) -> dict[str, Any] | None:
        source_resp = (
            self.db.table("generated_outputs").select("*").eq("id", source_id).limit(1).execute()
        )
        if not source_resp.data:
            return None
        outputs_resp = (
            self.db.table("generated_outputs")
            .select("*")
            .eq("parent_output_id", source_id)
            .order("created_at")
            .execute()
        )
        return {"source": source_resp.data[0], "outputs": list(outputs_resp.data or [])}


# ── Main entry points ──────────────────────────────────────────────────────────

def repurpose_content(
    req: RepurposeRequest,
    generator: ContentGenerator | None = None,
    repository: RepurposeRepository | None = None,
) -> RepurposeResult:
    """Full two-stage repurposing pipeline with Supabase persistence."""
    validate_request(req)

    active_generator = generator or ContentGenerator()
    repo = repository or RepurposeRepository()

    # Brand context (non-fatal)
    brand_block = ""
    if req.brand_profile_id:
        try:
            ctx = retrieve_brand_context(
                topic=req.source_title or req.source_text[:120],
                profile_id=req.brand_profile_id,
            )
            if ctx:
                brand_block = assemble_brand_block(ctx)
                logger.info("Brand context loaded profile_id=%s", req.brand_profile_id)
        except Exception as exc:
            logger.warning("Brand context retrieval failed (non-fatal): %s", exc)

    # Stage 1: extract structural meaning
    extraction = extract_meaning(req.source_text, req.source_type, active_generator)

    # Persist source
    source_id, created_at = repo.save_source(req, extraction)
    logger.info("Source persisted source_id=%s", source_id)

    # Stage 2: adapt for each target format
    outputs: list[RepurposedOutput] = []
    for fmt in req.target_formats:
        try:
            content = adapt_for_format(fmt, extraction, brand_block, req.language, active_generator)
        except (ContentGeneratorError, ValueError) as exc:
            logger.error("Format adaptation failed format=%s: %s", fmt, exc)
            content = f"[Generation failed: {exc}]"

        output_id = repo.save_output(req, source_id, fmt, content)
        meta = FORMAT_META[fmt]
        outputs.append(RepurposedOutput(
            output_id=output_id,
            format=fmt,
            label=meta["label"],
            content_type=meta["content_type"],
            channel=meta["channel"],
            content=content,
            word_count=len(content.split()),
            status="draft",
        ))

    logger.info(
        "Repurpose complete source_id=%s outputs=%s",
        source_id, len(outputs),
    )
    return RepurposeResult(
        source_id=source_id,
        extraction=extraction,
        outputs=outputs,
        created_at=created_at,
    )


def regenerate_output(
    source_id: str,
    output_id: str,
    fmt: str,
    extraction_raw: dict[str, Any],
    language: str = "english",
    brand_profile_id: str | None = None,
    generator: ContentGenerator | None = None,
    repository: RepurposeRepository | None = None,
) -> RepurposedOutput:
    """Regenerate one repurposed output and persist the updated content."""
    if fmt not in VALID_FORMATS:
        raise ValueError(f"Unknown format '{fmt}'.")

    active_generator = generator or ContentGenerator()
    repo = repository or RepurposeRepository()

    brand_block = ""
    if brand_profile_id:
        try:
            ctx = retrieve_brand_context(
                topic=extraction_raw.get("one_sentence_summary", ""),
                profile_id=brand_profile_id,
            )
            if ctx:
                brand_block = assemble_brand_block(ctx)
        except Exception as exc:
            logger.warning("Brand context retrieval failed for regeneration: %s", exc)

    prompt = format_prompt(fmt, extraction_raw, brand_block, language)
    content = active_generator.generate_content(prompt)
    repo.update_output(output_id, content)

    meta = FORMAT_META[fmt]
    logger.info("Output regenerated output_id=%s format=%s chars=%s", output_id, fmt, len(content))
    return RepurposedOutput(
        output_id=output_id,
        format=fmt,
        label=meta["label"],
        content_type=meta["content_type"],
        channel=meta["channel"],
        content=content,
        word_count=len(content.split()),
        status="draft",
    )
