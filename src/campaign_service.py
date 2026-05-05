"""
campaign_service.py

Campaign Generator — orchestrates the full two-stage AI pipeline and persists
every result to Supabase.

Flow:
  1. Validate inputs
  2. Retrieve brand context (optional)
  3. Load knowledge base context
  4. Stage 1  — generate campaign concept JSON
  5. Stage 2  — generate one asset per selected channel
  6. Persist  — campaigns → generated_outputs → campaign_items → calendar_draft
  7. Return   — CampaignResult (campaign_id + concept + assets)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal
from uuid import UUID

from dotenv import load_dotenv

from src.brand_intelligence import assemble_brand_block, retrieve_brand_context
from src.campaign_prompt_templates import (
    CHANNEL_CONTENT_TYPES,
    CHANNEL_LABELS,
    asset_prompt,
    concept_prompt,
)
from src.generation_service import load_knowledge_base
from src.llm_integration import ContentGenerator, ContentGeneratorError
from src.supabase_client import get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)

VALID_CHANNELS = {"linkedin", "instagram", "email", "blog", "ads"}
VALID_TONES = {"Academic", "Formal", "Professional", "Friendly", "Conversational"}


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class CampaignRequest:
    organization_id: str
    client_id: str
    project_id: str
    goal: str
    offer: str
    audience: str
    channels: list[str]
    start_date: str          # ISO date string "YYYY-MM-DD"
    end_date: str
    language: str = "english"
    tone: str = "Professional"
    kb_source: str = "hybrid"
    brand_profile_id: str | None = None
    created_by: str | None = None
    extra_context: str = ""   # optional pasted or uploaded context


@dataclass
class ContentIdea:
    id: int
    title: str
    channel: str
    format: str
    hook: str
    week: int


@dataclass
class CalendarEntry:
    week: int
    day: str
    channel: str
    title: str
    content_type: str


@dataclass
class CampaignConcept:
    name: str
    concept_summary: str
    core_message: str
    audience_angle: str
    channel_strategy: str
    content_ideas: list[ContentIdea]
    cta_suggestions: list[str]
    calendar_draft: list[CalendarEntry]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignAsset:
    asset_id: str
    campaign_item_id: str
    channel: str
    label: str
    content_type: str
    content: str
    status: str = "draft"


@dataclass
class CampaignResult:
    campaign_id: str
    concept: CampaignConcept
    assets: list[CampaignAsset]
    created_at: str


# ── Validation ─────────────────────────────────────────────────────────────────

def _validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID.") from exc
    return value


def validate_request(req: CampaignRequest) -> None:
    _validate_uuid(req.organization_id, "organization_id")
    _validate_uuid(req.client_id, "client_id")
    _validate_uuid(req.project_id, "project_id")
    if req.brand_profile_id:
        _validate_uuid(req.brand_profile_id, "brand_profile_id")
    if not req.goal.strip():
        raise ValueError("campaign goal is required.")
    if not req.offer.strip():
        raise ValueError("offer/service is required.")
    if not req.audience.strip():
        raise ValueError("target audience is required.")
    bad_channels = set(req.channels) - VALID_CHANNELS
    if bad_channels:
        raise ValueError(f"Unknown channels: {bad_channels}. Valid: {VALID_CHANNELS}")
    if not req.channels:
        raise ValueError("At least one channel must be selected.")


# ── Stage 1: Concept generation ───────────────────────────────────────────────

def _parse_concept(raw_json: str) -> CampaignConcept:
    """Parse LLM JSON response into a CampaignConcept, tolerating minor schema drift."""
    try:
        data = json.loads(raw_json.strip())
    except json.JSONDecodeError:
        # LLM sometimes wraps in a markdown fence — strip and retry
        stripped = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(stripped)

    ideas = [
        ContentIdea(
            id=int(item.get("id", idx + 1)),
            title=str(item.get("title", "")),
            channel=str(item.get("channel", "")),
            format=str(item.get("format", "")),
            hook=str(item.get("hook", "")),
            week=int(item.get("week", 1)),
        )
        for idx, item in enumerate(data.get("content_ideas") or [])
    ]

    calendar = [
        CalendarEntry(
            week=int(entry.get("week", 1)),
            day=str(entry.get("day", "Mon")),
            channel=str(entry.get("channel", "")),
            title=str(entry.get("title", "")),
            content_type=str(entry.get("content_type", "post")),
        )
        for entry in data.get("calendar_draft") or []
    ]

    return CampaignConcept(
        name=str(data.get("name", "Campaign")),
        concept_summary=str(data.get("concept_summary", "")),
        core_message=str(data.get("core_message", "")),
        audience_angle=str(data.get("audience_angle", "")),
        channel_strategy=str(data.get("channel_strategy", "")),
        content_ideas=ideas,
        cta_suggestions=list(data.get("cta_suggestions") or []),
        calendar_draft=calendar,
        raw=data,
    )


def generate_concept(
    req: CampaignRequest,
    kb_context: str,
    brand_block: str,
    generator: ContentGenerator,
) -> CampaignConcept:
    logger.info("Generating campaign concept goal='%s' channels=%s", req.goal, req.channels)
    prompt = concept_prompt(
        goal=req.goal,
        offer=req.offer,
        audience=req.audience,
        channels=req.channels,
        start_date=req.start_date,
        end_date=req.end_date,
        language=req.language,
        tone=req.tone,
        kb_context=kb_context,
        brand_block=brand_block,
    )
    raw = generator.generate_content(prompt)
    concept = _parse_concept(raw)
    logger.info("Campaign concept generated name='%s' ideas=%s", concept.name, len(concept.content_ideas))
    return concept


# ── Stage 2: Per-channel asset generation ─────────────────────────────────────

def generate_assets(
    req: CampaignRequest,
    concept: CampaignConcept,
    brand_block: str,
    generator: ContentGenerator,
) -> list[tuple[str, str, str]]:
    """
    Generate one asset per selected channel.
    Returns list of (channel, label, content) tuples.
    """
    results: list[tuple[str, str, str]] = []
    concept_dict = concept.raw

    for channel in req.channels:
        logger.info("Generating asset channel=%s", channel)
        try:
            prompt = asset_prompt(
                channel=channel,
                concept=concept_dict,
                brand_block=brand_block,
                language=req.language,
                extra_context=req.extra_context,
            )
            content = generator.generate_content(prompt)
            label = CHANNEL_LABELS.get(channel, channel.title())
            results.append((channel, label, content))
            logger.info("Asset generated channel=%s chars=%s", channel, len(content))
        except (ContentGeneratorError, ValueError) as exc:
            logger.error("Asset generation failed channel=%s: %s", channel, exc)
            results.append((channel, CHANNEL_LABELS.get(channel, channel), f"[Generation failed: {exc}]"))

    return results


# ── Supabase persistence ───────────────────────────────────────────────────────

class CampaignRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.db = client or get_supabase_admin_client()

    def save_campaign(self, req: CampaignRequest, concept: CampaignConcept) -> str:
        payload = {
            "organization_id": req.organization_id,
            "client_id": req.client_id,
            "project_id": req.project_id,
            "name": concept.name,
            "objective": req.goal,
            "audience": req.audience,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "status": "active",
            "tone": req.tone,
            "offer": req.offer,
            "channels": req.channels,
            "concept": concept.concept_summary,
            "core_message": concept.core_message,
            "audience_angle": concept.audience_angle,
            "channel_strategy": concept.channel_strategy,
            "cta_suggestions": concept.cta_suggestions,
            "content_ideas": [
                {
                    "id": idea.id,
                    "title": idea.title,
                    "channel": idea.channel,
                    "format": idea.format,
                    "hook": idea.hook,
                    "week": idea.week,
                }
                for idea in concept.content_ideas
            ],
            "calendar_draft": [
                {
                    "week": e.week,
                    "day": e.day,
                    "channel": e.channel,
                    "title": e.title,
                    "content_type": e.content_type,
                }
                for e in concept.calendar_draft
            ],
            "brand_profile_id": req.brand_profile_id,
            "created_by": req.created_by,
            "metadata": {"language": req.language, "kb_source": req.kb_source},
        }
        response = self.db.table("campaigns").insert(payload).execute()
        campaign_id = str(response.data[0]["id"])
        logger.info("Campaign saved campaign_id=%s", campaign_id)
        return campaign_id

    def save_asset(
        self,
        req: CampaignRequest,
        campaign_id: str,
        channel: str,
        label: str,
        content: str,
    ) -> tuple[str, str]:
        """Save to generated_outputs + campaign_items. Returns (asset_id, item_id)."""
        content_type = CHANNEL_CONTENT_TYPES.get(channel, "other")
        output_payload = {
            "organization_id": req.organization_id,
            "client_id": req.client_id,
            "project_id": req.project_id,
            "campaign_id": campaign_id,
            "brand_profile_id": req.brand_profile_id,
            "title": label,
            "content": content,
            "content_type": content_type,
            "channel": channel if channel in {
                "website", "linkedin", "instagram", "facebook", "x",
                "email", "newsletter", "ads", "blog", "other"
            } else "other",
            "language": req.language,
            "status": "draft",
            "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
            "word_count": len(content.split()),
            "metadata": {"channel": channel, "tone": req.tone},
            "created_by": req.created_by,
        }
        output_response = self.db.table("generated_outputs").insert(output_payload).execute()
        asset_id = str(output_response.data[0]["id"])

        # Compute a rough due date based on calendar_draft or default to start + 3 days
        try:
            start = date.fromisoformat(req.start_date)
            due = start + timedelta(days=3)
        except ValueError:
            due = date.today() + timedelta(days=3)

        item_payload = {
            "organization_id": req.organization_id,
            "client_id": req.client_id,
            "project_id": req.project_id,
            "campaign_id": campaign_id,
            "output_id": asset_id,
            "title": label,
            "content_type": content_type,
            "channel": output_payload["channel"],
            "status": "draft",
            "due_date": due.isoformat(),
        }
        item_response = self.db.table("campaign_items").insert(item_payload).execute()
        item_id = str(item_response.data[0]["id"])
        logger.info("Asset saved asset_id=%s item_id=%s channel=%s", asset_id, item_id, channel)
        return asset_id, item_id

    def get_campaign(self, campaign_id: str) -> dict[str, Any] | None:
        response = self.db.table("campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        return response.data[0] if response.data else None

    def get_campaign_assets(self, campaign_id: str) -> list[dict[str, Any]]:
        response = (
            self.db.table("generated_outputs")
            .select("*")
            .eq("campaign_id", campaign_id)
            .order("created_at")
            .execute()
        )
        return list(response.data or [])

    def list_campaigns(self, client_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        query = (
            self.db.table("campaigns")
            .select("id,name,objective,audience,channels,status,start_date,end_date,created_at")
            .eq("client_id", client_id)
            .order("created_at", desc=True)
        )
        if project_id:
            query = query.eq("project_id", project_id)
        return list(query.execute().data or [])

    def update_asset(self, asset_id: str, content: str) -> dict[str, Any]:
        payload = {"content": content, "word_count": len(content.split()), "status": "draft"}
        response = self.db.table("generated_outputs").update(payload).eq("id", asset_id).execute()
        return response.data[0]


# ── Main entry points ──────────────────────────────────────────────────────────

def generate_campaign(
    req: CampaignRequest,
    generator: ContentGenerator | None = None,
    repository: CampaignRepository | None = None,
) -> CampaignResult:
    """Full two-stage campaign generation + persistence."""
    validate_request(req)

    active_generator = generator or ContentGenerator()
    repo = repository or CampaignRepository()

    # Brand context (non-fatal if unavailable)
    brand_block = ""
    if req.brand_profile_id:
        try:
            ctx = retrieve_brand_context(topic=req.goal, profile_id=req.brand_profile_id)
            if ctx:
                brand_block = assemble_brand_block(ctx)
                logger.info("Brand context loaded profile_id=%s", req.brand_profile_id)
        except Exception as exc:
            logger.warning("Brand context retrieval failed (non-fatal): %s", exc)

    # Knowledge base context
    kb_context = ""
    try:
        kb_context, _ = load_knowledge_base(req.kb_source)  # type: ignore[arg-type]
    except Exception as exc:
        logger.warning("KB load failed (non-fatal): %s", exc)

    # Stage 1: concept
    concept = generate_concept(req, kb_context, brand_block, active_generator)

    # Persist campaign
    campaign_id = repo.save_campaign(req, concept)

    # Stage 2: per-channel assets
    raw_assets = generate_assets(req, concept, brand_block, active_generator)

    # Persist assets
    saved_assets: list[CampaignAsset] = []
    for channel, label, content in raw_assets:
        asset_id, item_id = repo.save_asset(req, campaign_id, channel, label, content)
        saved_assets.append(CampaignAsset(
            asset_id=asset_id,
            campaign_item_id=item_id,
            channel=channel,
            label=label,
            content_type=CHANNEL_CONTENT_TYPES.get(channel, "other"),
            content=content,
            status="draft",
        ))

    campaign_row = repo.get_campaign(campaign_id)
    created_at = campaign_row["created_at"] if campaign_row else ""

    logger.info(
        "Campaign generation complete campaign_id=%s concept='%s' assets=%s",
        campaign_id, concept.name, len(saved_assets),
    )
    return CampaignResult(
        campaign_id=campaign_id,
        concept=concept,
        assets=saved_assets,
        created_at=created_at,
    )


def regenerate_asset(
    campaign_id: str,
    asset_id: str,
    channel: str,
    concept_raw: dict[str, Any],
    language: str = "english",
    brand_profile_id: str | None = None,
    extra_context: str = "",
    generator: ContentGenerator | None = None,
    repository: CampaignRepository | None = None,
) -> CampaignAsset:
    """Regenerate a single campaign asset and persist the updated content."""
    active_generator = generator or ContentGenerator()
    repo = repository or CampaignRepository()

    brand_block = ""
    if brand_profile_id:
        try:
            ctx = retrieve_brand_context(topic=concept_raw.get("core_message", ""), profile_id=brand_profile_id)
            if ctx:
                brand_block = assemble_brand_block(ctx)
        except Exception as exc:
            logger.warning("Brand context retrieval failed for regeneration: %s", exc)

    prompt = asset_prompt(channel=channel, concept=concept_raw, brand_block=brand_block,
                          language=language, extra_context=extra_context)
    content = active_generator.generate_content(prompt)

    repo.update_asset(asset_id, content)
    label = CHANNEL_LABELS.get(channel, channel.title())
    logger.info("Asset regenerated asset_id=%s channel=%s chars=%s", asset_id, channel, len(content))
    return CampaignAsset(
        asset_id=asset_id,
        campaign_item_id="",
        channel=channel,
        label=label,
        content_type=CHANNEL_CONTENT_TYPES.get(channel, "other"),
        content=content,
        status="draft",
    )
