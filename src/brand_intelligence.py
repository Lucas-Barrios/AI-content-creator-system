"""
brand_intelligence.py

Brand Intelligence Layer — retrieves, assembles, and evaluates brand context
so that every content generation request is automatically conditioned on the
client's brand voice, positioning, audience, and approved examples.

Three public entry points:
  retrieve_brand_context    — fetch BrandProfile + relevant brand RAG chunks
  assemble_brand_block      — format profile into an injectable prompt section
  score_brand_consistency   — LLM-as-judge evaluation of generated output
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from dotenv import load_dotenv

from src.supabase_client import get_supabase_admin_client

load_dotenv()
logger = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class BrandProfile:
    id: str
    organization_id: str
    client_id: str
    project_id: str | None
    name: str
    positioning: str | None
    voice: str | None
    tone_guidelines: str | None
    audience_summary: str | None
    value_proposition: str | None
    approved_terms: list[str]
    banned_terms: list[str]
    compliance_notes: str | None
    brand_values: list[str]
    example_good: list[str]
    example_bad: list[str]
    is_default: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "BrandProfile":
        return cls(
            id=str(row["id"]),
            organization_id=str(row["organization_id"]),
            client_id=str(row["client_id"]),
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            name=row.get("name") or "Default",
            positioning=row.get("positioning"),
            voice=row.get("voice"),
            tone_guidelines=row.get("tone_guidelines"),
            audience_summary=row.get("audience_summary"),
            value_proposition=row.get("value_proposition"),
            approved_terms=list(row.get("approved_terms") or []),
            banned_terms=list(row.get("banned_terms") or []),
            compliance_notes=row.get("compliance_notes"),
            brand_values=list(row.get("brand_values") or []),
            example_good=list(row.get("example_good") or []),
            example_bad=list(row.get("example_bad") or []),
            is_default=bool(row.get("is_default", False)),
            metadata=dict(row.get("metadata") or {}),
        )


@dataclass
class BrandContext:
    profile: BrandProfile
    brand_chunks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BrandConsistencyScore:
    overall_score: float
    voice_score: float
    terminology_score: float
    audience_score: float
    violations: list[str]
    suggestions: list[str]
    verdict: Literal["approved", "needs_revision"]


# ── Repository protocol + Supabase implementation ─────────────────────────────

class BrandRepository(Protocol):
    def get_profile(self, profile_id: str) -> dict[str, Any] | None: ...
    def list_profiles(self, client_id: str, project_id: str | None) -> list[dict[str, Any]]: ...
    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def update_profile(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_default_profile(self, client_id: str, project_id: str | None) -> dict[str, Any] | None: ...


class SupabaseBrandRepository:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or get_supabase_admin_client()

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("brand_profiles")
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def list_profiles(self, client_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        query = (
            self.client.table("brand_profiles")
            .select("*")
            .eq("client_id", client_id)
            .order("is_default", desc=True)
            .order("created_at", desc=True)
        )
        if project_id:
            query = query.eq("project_id", project_id)
        return list(query.execute().data or [])

    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("brand_profiles").insert(payload).execute()
        return response.data[0]

    def update_profile(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table("brand_profiles")
            .update(payload)
            .eq("id", profile_id)
            .execute()
        )
        return response.data[0]

    def get_default_profile(self, client_id: str, project_id: str | None = None) -> dict[str, Any] | None:
        query = (
            self.client.table("brand_profiles")
            .select("*")
            .eq("client_id", client_id)
            .eq("is_default", True)
            .limit(1)
        )
        if project_id:
            query = query.eq("project_id", project_id)
        response = query.execute()
        return response.data[0] if response.data else None


# ── Brand chunk retrieval ──────────────────────────────────────────────────────

def _retrieve_brand_chunks(
    profile: BrandProfile,
    topic: str,
    max_chunks: int = 6,
) -> list[dict[str, Any]]:
    """
    Retrieve brand-tagged knowledge chunks relevant to the topic via pgvector similarity.
    Falls back to an empty list if Supabase/embeddings are not configured.
    """
    if not topic.strip():
        return []

    try:
        from src.rag_ingestion import OpenAIEmbeddingProvider, SupabaseKnowledgeRepository
        embedder = OpenAIEmbeddingProvider()
        repo = SupabaseKnowledgeRepository()
        embedding = embedder.embed_texts([topic])[0]
        all_chunks = repo.match_chunks(
            query_embedding=embedding,
            client_id=profile.client_id,
            project_id=profile.project_id,
            match_count=max_chunks * 3,  # over-fetch so filtering still returns enough
            match_threshold=0.60,
        )
        brand_chunks = [c for c in all_chunks if c.get("source_kind") == "brand"]
        return brand_chunks[:max_chunks]
    except Exception as exc:
        logger.warning("Brand chunk retrieval skipped: %s", exc)
        return []


# ── Public API ─────────────────────────────────────────────────────────────────

def retrieve_brand_context(
    topic: str,
    profile_id: str | None = None,
    client_id: str | None = None,
    project_id: str | None = None,
    repository: BrandRepository | None = None,
) -> BrandContext | None:
    """
    Fetch the brand profile and relevant brand chunks for a generation request.

    Resolution order:
      1. profile_id (exact lookup)
      2. client_id + project_id default profile
      3. client_id-only default profile
    Returns None if no profile is found.
    """
    repo = repository or SupabaseBrandRepository()

    row: dict[str, Any] | None = None
    if profile_id:
        row = repo.get_profile(profile_id)
    elif client_id:
        row = repo.get_default_profile(client_id, project_id)

    if not row:
        return None

    profile = BrandProfile.from_row(row)
    chunks = _retrieve_brand_chunks(profile, topic)
    logger.info(
        "Brand context retrieved profile_id=%s client_id=%s brand_chunks=%s",
        profile.id, profile.client_id, len(chunks),
    )
    return BrandContext(profile=profile, brand_chunks=chunks)


def assemble_brand_block(ctx: BrandContext) -> str:
    """
    Format a BrandContext into a structured prompt block to prepend to any
    generation request. Returns an empty string if the context is empty.
    """
    p = ctx.profile
    lines: list[str] = ["--- BRAND INTELLIGENCE ---"]

    lines.append(f"Brand Profile   : {p.name}")
    if p.positioning:
        lines.append(f"Positioning     : {p.positioning}")
    if p.value_proposition:
        lines.append(f"Value Prop      : {p.value_proposition}")
    if p.audience_summary:
        lines.append(f"Target Audience : {p.audience_summary}")

    if p.voice:
        lines.append(f"\nVoice & Tone    : {p.voice}")
    if p.tone_guidelines:
        lines.append(f"Tone Guidelines :\n{p.tone_guidelines}")

    if p.brand_values:
        lines.append(f"\nBrand Values    : {', '.join(p.brand_values)}")
    if p.approved_terms:
        lines.append(f"Preferred Terms : {', '.join(p.approved_terms)}")
    if p.banned_terms:
        lines.append(f"NEVER USE       : {', '.join(p.banned_terms)}")
    if p.compliance_notes:
        lines.append(f"Compliance      : {p.compliance_notes}")

    if p.example_good:
        lines.append("\nGOOD CONTENT EXAMPLES (match this style):")
        for i, ex in enumerate(p.example_good[:3], 1):
            lines.append(f"  [{i}] {ex}")

    if p.example_bad:
        lines.append("\nBAD CONTENT EXAMPLES (do NOT write like this):")
        for i, ex in enumerate(p.example_bad[:3], 1):
            lines.append(f"  [{i}] {ex}")

    if ctx.brand_chunks:
        lines.append("\nRELEVANT BRAND KNOWLEDGE:")
        for chunk in ctx.brand_chunks:
            snippet = chunk.get("content", "")[:300].replace("\n", " ")
            lines.append(f"  • {snippet}")

    lines.append("--- END BRAND INTELLIGENCE ---\n")
    return "\n".join(lines)


# ── Brand consistency scorer ───────────────────────────────────────────────────

_SCORE_SYSTEM = """\
You are a brand consistency evaluator. You receive a brand profile and a piece of generated content.
Score the content strictly and return ONLY valid JSON — no markdown fences, no extra text.

Required JSON shape:
{
  "overall_score":      <0-10 float>,
  "voice_score":        <0-10 float>,
  "terminology_score":  <0-10 float>,
  "audience_score":     <0-10 float>,
  "violations":         [<string>, ...],
  "suggestions":        [<string>, ...],
  "verdict":            "approved" | "needs_revision"
}

Scoring guide:
- voice_score       : Does the tone, register, and style match the brand voice?
- terminology_score : Are preferred terms used? Are banned terms absent?
- audience_score    : Is the content pitched at the stated target audience?
- overall_score     : Weighted average, your holistic judgement.
- violations        : Specific rule breaks (mention the rule and the offending text).
- suggestions       : Concrete rewrites or fixes (max 3).
- verdict           : "approved" if overall_score >= 7, else "needs_revision".\
"""


def score_brand_consistency(
    content: str,
    ctx: BrandContext,
    generator: Any | None = None,
) -> BrandConsistencyScore:
    """
    Evaluate generated content against the brand profile using GPT as judge.

    Args:
        content   : The generated text to evaluate.
        ctx       : BrandContext holding the profile to evaluate against.
        generator : Optional ContentGenerator override (uses default if None).

    Returns:
        BrandConsistencyScore with per-dimension scores, violations, and verdict.
    """
    from src.llm_integration import ContentGenerator, ContentGeneratorError

    p = ctx.profile
    brand_summary_lines = [
        f"Brand Profile   : {p.name}",
        f"Positioning     : {p.positioning or '—'}",
        f"Value Prop      : {p.value_proposition or '—'}",
        f"Audience        : {p.audience_summary or '—'}",
        f"Voice & Tone    : {p.voice or '—'}",
        f"Tone Guidelines : {p.tone_guidelines or '—'}",
        f"Brand Values    : {', '.join(p.brand_values) or '—'}",
        f"Preferred Terms : {', '.join(p.approved_terms) or '—'}",
        f"Banned Terms    : {', '.join(p.banned_terms) or '—'}",
    ]
    brand_summary = "\n".join(brand_summary_lines)

    prompt = (
        f"{_SCORE_SYSTEM}\n\n"
        f"BRAND PROFILE:\n{brand_summary}\n\n"
        f"GENERATED CONTENT:\n{content}\n\n"
        "Return your evaluation as JSON now:"
    )

    active_generator = generator or ContentGenerator()
    try:
        raw = active_generator.generate_content(prompt)
        data = json.loads(raw.strip())
    except (ContentGeneratorError, json.JSONDecodeError) as exc:
        logger.error("Brand scoring failed: %s", exc)
        return BrandConsistencyScore(
            overall_score=0.0,
            voice_score=0.0,
            terminology_score=0.0,
            audience_score=0.0,
            violations=["Scoring failed — the evaluator returned an unreadable response."],
            suggestions=[],
            verdict="needs_revision",
        )

    return BrandConsistencyScore(
        overall_score=float(data.get("overall_score", 0)),
        voice_score=float(data.get("voice_score", 0)),
        terminology_score=float(data.get("terminology_score", 0)),
        audience_score=float(data.get("audience_score", 0)),
        violations=list(data.get("violations") or []),
        suggestions=list(data.get("suggestions") or []),
        verdict=data.get("verdict", "needs_revision"),
    )


# ── Convenience helpers ────────────────────────────────────────────────────────

def build_brand_profile_payload(
    organization_id: str,
    client_id: str,
    project_id: str | None,
    name: str,
    *,
    positioning: str | None = None,
    voice: str | None = None,
    tone_guidelines: str | None = None,
    audience_summary: str | None = None,
    value_proposition: str | None = None,
    approved_terms: list[str] | None = None,
    banned_terms: list[str] | None = None,
    compliance_notes: str | None = None,
    brand_values: list[str] | None = None,
    example_good: list[str] | None = None,
    example_bad: list[str] | None = None,
    is_default: bool = False,
    created_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a clean insert/update payload for brand_profiles."""
    return {
        k: v for k, v in {
            "organization_id": organization_id,
            "client_id": client_id,
            "project_id": project_id,
            "name": name,
            "positioning": positioning,
            "voice": voice,
            "tone_guidelines": tone_guidelines,
            "audience_summary": audience_summary,
            "value_proposition": value_proposition,
            "approved_terms": approved_terms or [],
            "banned_terms": banned_terms or [],
            "compliance_notes": compliance_notes,
            "brand_values": brand_values or [],
            "example_good": example_good or [],
            "example_bad": example_bad or [],
            "is_default": is_default,
            "created_by": created_by,
            "metadata": metadata or {},
        }.items()
        if v is not None or k in {
            "approved_terms", "banned_terms", "brand_values",
            "example_good", "example_bad", "is_default", "metadata",
        }
    }
