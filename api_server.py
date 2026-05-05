"""
FastAPI backend for the Next.js frontend.

Run locally:
  uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

from collections.abc import AsyncIterator
import logging
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from src.api_helpers import (
    build_chat_prompt,
    feedback_record_to_response,
    normalize_content_type,
    safe_download_filename,
    sources_to_dicts,
    uploaded_files_to_dicts,
    validate_choice,
)
from src.brand_intelligence import (
    BrandConsistencyScore,
    SupabaseBrandRepository,
    assemble_brand_block,
    build_brand_profile_payload,
    retrieve_brand_context,
    score_brand_consistency,
)
from src.content_artifacts import compare_uniqueness, make_docx_bytes
from src.generation_service import (
    GenerateContentRequest,
    UploadedFileRef,
    generate_content,
    save_uploads,
)
from src.feedback_repository import FeedbackRecord, get_feedback_repository
from src.logging_config import configure_logging
from src.llm_integration import ContentGenerator, ContentGeneratorError
from src.rag_ingestion import (
    KnowledgeSourceInput,
    RagIngestionError,
    RagIngestionService,
    search_knowledge_chunks,
)

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="SRH AI Content Creator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UploadedFileBody(BaseModel):
    id: str
    name: str
    size: int
    contentType: str
    url: Optional[str] = None


class GenerateBody(BaseModel):
    content_type: Optional[str] = Field(default=None, alias="contentType")
    topic: str
    audience: str = "Prospective Students"
    language: str = "english"
    tone: str = "Professional"
    length: str = "Medium"
    knowledge_base: str = Field(default="hybrid", alias="knowledgeBase")
    files: list[UploadedFileBody] = Field(default_factory=list)
    feedback: str = ""
    previousContent: str = ""
    brand_profile_id: Optional[str] = Field(default=None, alias="brandProfileId")


class FeedbackBody(BaseModel):
    generationId: str
    status: str
    comment: str = ""
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)


class ContentArtifactBody(BaseModel):
    content: str
    topic: str = "SRH Content"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


class BrandProfileCreateBody(BaseModel):
    organization_id: str = Field(alias="organizationId")
    client_id: str = Field(alias="clientId")
    project_id: Optional[str] = Field(default=None, alias="projectId")
    name: str = "Default Brand Profile"
    positioning: Optional[str] = None
    voice: Optional[str] = None
    tone_guidelines: Optional[str] = Field(default=None, alias="toneGuidelines")
    audience_summary: Optional[str] = Field(default=None, alias="audienceSummary")
    value_proposition: Optional[str] = Field(default=None, alias="valueProposition")
    approved_terms: list[str] = Field(default_factory=list, alias="approvedTerms")
    banned_terms: list[str] = Field(default_factory=list, alias="bannedTerms")
    compliance_notes: Optional[str] = Field(default=None, alias="complianceNotes")
    brand_values: list[str] = Field(default_factory=list, alias="brandValues")
    example_good: list[str] = Field(default_factory=list, alias="exampleGood")
    example_bad: list[str] = Field(default_factory=list, alias="exampleBad")
    is_default: bool = Field(default=False, alias="isDefault")
    created_by: Optional[str] = Field(default=None, alias="createdBy")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class BrandProfileUpdateBody(BaseModel):
    name: Optional[str] = None
    positioning: Optional[str] = None
    voice: Optional[str] = None
    tone_guidelines: Optional[str] = Field(default=None, alias="toneGuidelines")
    audience_summary: Optional[str] = Field(default=None, alias="audienceSummary")
    value_proposition: Optional[str] = Field(default=None, alias="valueProposition")
    approved_terms: Optional[list[str]] = Field(default=None, alias="approvedTerms")
    banned_terms: Optional[list[str]] = Field(default=None, alias="bannedTerms")
    compliance_notes: Optional[str] = Field(default=None, alias="complianceNotes")
    brand_values: Optional[list[str]] = Field(default=None, alias="brandValues")
    example_good: Optional[list[str]] = Field(default=None, alias="exampleGood")
    example_bad: Optional[list[str]] = Field(default=None, alias="exampleBad")
    is_default: Optional[bool] = Field(default=None, alias="isDefault")
    metadata: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


class BrandScoreBody(BaseModel):
    content: str
    brand_profile_id: str = Field(alias="brandProfileId")
    topic: str = ""

    model_config = {"populate_by_name": True}


class KnowledgeTextBody(BaseModel):
    organization_id: str = Field(alias="organizationId")
    client_id: str = Field(alias="clientId")
    project_id: Optional[str] = Field(default=None, alias="projectId")
    title: str
    text: str
    source_kind: str = Field(default="other", alias="sourceKind")
    content_type: Optional[str] = Field(default=None, alias="contentType")
    language: Optional[str] = None
    channel: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    uploaded_by: Optional[str] = Field(default=None, alias="uploadedBy")


class KnowledgeSearchBody(BaseModel):
    query: str
    client_id: Optional[str] = Field(default=None, alias="clientId")
    project_id: Optional[str] = Field(default=None, alias="projectId")
    content_type: Optional[str] = Field(default=None, alias="contentType")
    language: Optional[str] = None
    channel: Optional[str] = None
    match_count: int = Field(default=8, alias="matchCount")
    match_threshold: float = Field(default=0.72, alias="matchThreshold")


SOURCE_KINDS = {"brand", "product", "audience", "market", "competitor", "campaign", "policy", "other"}
RAG_CONTENT_TYPES = {"blog", "social", "email", "newsletter", "ad", "landing_page", "program", "other"}
CHANNELS = {"website", "linkedin", "instagram", "facebook", "x", "email", "newsletter", "ads", "blog", "other"}


def _request_from_body(body: GenerateBody) -> GenerateContentRequest:
    logger.info("Validating generate request for topic='%s'", body.topic)
    try:
        content_type = validate_choice(
            normalize_content_type(body.content_type),
            {"blog", "social", "program", "newsletter"},
            "contentType",
        )
        language = validate_choice(body.language, {"english", "german"}, "language")
        knowledge_base = validate_choice(body.knowledge_base, {"hybrid", "primary", "secondary"}, "knowledgeBase")
        length = validate_choice(body.length, {"Short", "Medium", "Long"}, "length")
    except ValueError as error:
        logger.error("Generate request validation failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error

    logger.info(
        "Generate request validated: content_type=%s language=%s knowledge_base=%s length=%s",
        content_type,
        language,
        knowledge_base,
        length,
    )
    return GenerateContentRequest(
        contentType=content_type,  # type: ignore[arg-type]
        topic=body.topic,
        audience=body.audience,
        language=language,  # type: ignore[arg-type]
        tone=body.tone,
        length=length,  # type: ignore[arg-type]
        knowledgeBase=knowledge_base,  # type: ignore[arg-type]
        files=[
            UploadedFileRef(
                id=file.id,
                name=file.name,
                size=file.size,
                contentType=file.contentType,
                url=file.url,
            )
            for file in body.files
        ],
        feedback=body.feedback,
        previousContent=body.previousContent,
        brand_profile_id=body.brand_profile_id,
    )


def _normalize_optional_choice(value: str | None, allowed: set[str], field_name: str) -> str | None:
    if value is None or value == "":
        return None
    return validate_choice(value, allowed, field_name)


def _knowledge_source_from_text_body(body: KnowledgeTextBody) -> KnowledgeSourceInput:
    return KnowledgeSourceInput(
        organization_id=body.organization_id,
        client_id=body.client_id,
        project_id=body.project_id,
        title=body.title,
        text=body.text,
        source_kind=validate_choice(body.source_kind, SOURCE_KINDS, "sourceKind"),  # type: ignore[arg-type]
        content_type=_normalize_optional_choice(body.content_type, RAG_CONTENT_TYPES, "contentType"),  # type: ignore[arg-type]
        language=body.language,
        channel=_normalize_optional_choice(body.channel, CHANNELS, "channel"),  # type: ignore[arg-type]
        tags=body.tags,
        metadata=body.metadata,
        uploaded_by=body.uploaded_by,
    )


def _ingestion_response(result: Any) -> dict[str, Any]:
    return {
        "documentId": result.document_id,
        "duplicate": result.duplicate,
        "contentHash": result.content_hash,
        "chunkCount": result.chunk_count,
        "embeddingCount": result.embedding_count,
        "status": result.status,
        "message": result.message,
    }


@app.get("/health")
def health() -> dict[str, str]:
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.post("/generate")
def generate(body: GenerateBody) -> dict[str, Any]:
    logger.info("Received /generate request topic='%s'", body.topic)
    try:
        request = _request_from_body(body)
        result = generate_content(request)
        logger.info(
            "Generated content successfully topic='%s' sources=%s content_chars=%s",
            request.topic,
            len(result.sources),
            len(result.content),
        )
        return {
            "content": result.content,
            "sources": sources_to_dicts(result.sources),
            "brief": result.brief,
        }
    except HTTPException:
        raise
    except ContentGeneratorError as error:
        logger.error("Generation API error for topic='%s': %s", body.topic, error)
        raise HTTPException(status_code=502, detail=str(error)) from error
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        logger.error("Generation request failed for topic='%s': %s", body.topic, error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected generation error for topic='%s'", body.topic)
        raise HTTPException(status_code=500, detail=f"Unexpected backend error: {error}") from error


@app.post("/upload")
async def upload(files: list[UploadFile] = File(default=[])) -> dict[str, list[dict[str, Any]]]:
    logger.info("Received /upload request files=%s", len(files))
    stored_files: list[tuple[str, bytes, str]] = []
    for file in files:
        content = await file.read()
        logger.info("Read uploaded file name='%s' bytes=%s type='%s'", file.filename, len(content), file.content_type)
        stored_files.append((file.filename or "upload", content, file.content_type or ""))

    uploaded = save_uploads(stored_files)
    logger.info("Upload request completed files=%s", len(uploaded))
    return {"files": uploaded_files_to_dicts(uploaded)}


@app.post("/knowledge/ingest-text")
def ingest_knowledge_text(body: KnowledgeTextBody) -> dict[str, Any]:
    logger.info("Received /knowledge/ingest-text title='%s' client_id=%s", body.title, body.client_id)
    try:
        source = _knowledge_source_from_text_body(body)
        result = RagIngestionService().ingest(source)
        return _ingestion_response(result)
    except (ValueError, RagIngestionError) as error:
        logger.error("Knowledge text ingestion failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected knowledge text ingestion error")
        raise HTTPException(status_code=500, detail=f"Unexpected ingestion error: {error}") from error


@app.post("/knowledge/ingest-file")
async def ingest_knowledge_file(
    organization_id: str = Form(alias="organizationId"),
    client_id: str = Form(alias="clientId"),
    project_id: Optional[str] = Form(default=None, alias="projectId"),
    title: str = Form(),
    source_kind: str = Form(default="other", alias="sourceKind"),
    content_type: Optional[str] = Form(default=None, alias="contentType"),
    language: Optional[str] = Form(default=None),
    channel: Optional[str] = Form(default=None),
    tags: str = Form(default=""),
    uploaded_by: Optional[str] = Form(default=None, alias="uploadedBy"),
    file: UploadFile = File(),
) -> dict[str, Any]:
    logger.info("Received /knowledge/ingest-file title='%s' filename='%s' client_id=%s", title, file.filename, client_id)
    try:
        file_bytes = await file.read()
        source = KnowledgeSourceInput(
            organization_id=organization_id,
            client_id=client_id,
            project_id=project_id,
            title=title,
            file_bytes=file_bytes,
            filename=file.filename or "upload",
            mime_type=file.content_type,
            source_kind=validate_choice(source_kind, SOURCE_KINDS, "sourceKind"),  # type: ignore[arg-type]
            content_type=_normalize_optional_choice(content_type, RAG_CONTENT_TYPES, "contentType"),  # type: ignore[arg-type]
            language=language,
            channel=_normalize_optional_choice(channel, CHANNELS, "channel"),  # type: ignore[arg-type]
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
            uploaded_by=uploaded_by,
        )
        result = RagIngestionService().ingest(source)
        return _ingestion_response(result)
    except (ValueError, RagIngestionError) as error:
        logger.error("Knowledge file ingestion failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected knowledge file ingestion error")
        raise HTTPException(status_code=500, detail=f"Unexpected ingestion error: {error}") from error


@app.post("/knowledge/search")
def search_knowledge(body: KnowledgeSearchBody) -> dict[str, Any]:
    logger.info("Received /knowledge/search client_id=%s project_id=%s query_chars=%s", body.client_id, body.project_id, len(body.query))
    try:
        matches = search_knowledge_chunks(
            query=body.query,
            client_id=body.client_id,
            project_id=body.project_id,
            content_type=_normalize_optional_choice(body.content_type, RAG_CONTENT_TYPES, "contentType"),
            language=body.language,
            channel=_normalize_optional_choice(body.channel, CHANNELS, "channel"),
            match_count=body.match_count,
            match_threshold=body.match_threshold,
        )
        return {"matches": matches, "count": len(matches)}
    except (ValueError, RagIngestionError) as error:
        logger.error("Knowledge search failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected knowledge search error")
        raise HTTPException(status_code=500, detail=f"Unexpected search error: {error}") from error


@app.post("/feedback")
def feedback(body: FeedbackBody) -> dict[str, Any]:
    logger.info("Received /feedback request generation_id=%s status=%s", body.generationId, body.status)
    try:
        status = validate_choice(body.status, {"approved", "needs_revision"}, "feedback status")
    except ValueError as error:
        logger.error("Feedback validation failed generation_id=%s: %s", body.generationId, error)
        raise HTTPException(status_code=400, detail=str(error)) from error

    record = FeedbackRecord(
        generation_id=body.generationId,
        status=status,  # type: ignore[arg-type]
        comment=body.comment,
        request=body.request,
        response=body.response,
    )
    saved = get_feedback_repository().save(record)
    logger.info("Feedback saved id=%s generation_id=%s status=%s", saved.id, saved.generation_id, saved.status)
    return feedback_record_to_response(saved)


@app.post("/brand/profiles")
def create_brand_profile(body: BrandProfileCreateBody) -> dict[str, Any]:
    logger.info("Received /brand/profiles POST client_id=%s name='%s'", body.client_id, body.name)
    try:
        repo = SupabaseBrandRepository()
        payload = build_brand_profile_payload(
            organization_id=body.organization_id,
            client_id=body.client_id,
            project_id=body.project_id,
            name=body.name,
            positioning=body.positioning,
            voice=body.voice,
            tone_guidelines=body.tone_guidelines,
            audience_summary=body.audience_summary,
            value_proposition=body.value_proposition,
            approved_terms=body.approved_terms,
            banned_terms=body.banned_terms,
            compliance_notes=body.compliance_notes,
            brand_values=body.brand_values,
            example_good=body.example_good,
            example_bad=body.example_bad,
            is_default=body.is_default,
            created_by=body.created_by,
            metadata=body.metadata,
        )
        row = repo.create_profile(payload)
        logger.info("Brand profile created id=%s", row["id"])
        return row
    except Exception as error:
        logger.exception("Brand profile creation failed")
        raise HTTPException(status_code=500, detail=f"Brand profile creation failed: {error}") from error


@app.get("/brand/profiles")
def list_brand_profiles(
    clientId: str,
    projectId: Optional[str] = None,
) -> dict[str, Any]:
    logger.info("Received /brand/profiles GET client_id=%s project_id=%s", clientId, projectId)
    try:
        repo = SupabaseBrandRepository()
        profiles = repo.list_profiles(clientId, projectId)
        return {"profiles": profiles, "count": len(profiles)}
    except Exception as error:
        logger.exception("Brand profile list failed")
        raise HTTPException(status_code=500, detail=f"Brand profile list failed: {error}") from error


@app.get("/brand/profiles/{profile_id}")
def get_brand_profile(profile_id: str) -> dict[str, Any]:
    logger.info("Received /brand/profiles/%s GET", profile_id)
    try:
        repo = SupabaseBrandRepository()
        row = repo.get_profile(profile_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Brand profile '{profile_id}' not found.")
        return row
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Brand profile fetch failed profile_id=%s", profile_id)
        raise HTTPException(status_code=500, detail=f"Brand profile fetch failed: {error}") from error


@app.put("/brand/profiles/{profile_id}")
def update_brand_profile(profile_id: str, body: BrandProfileUpdateBody) -> dict[str, Any]:
    logger.info("Received /brand/profiles/%s PUT", profile_id)
    try:
        repo = SupabaseBrandRepository()
        # Build payload from non-None fields only
        payload: dict[str, Any] = {}
        alias_map = {
            "tone_guidelines": "tone_guidelines",
            "audience_summary": "audience_summary",
            "value_proposition": "value_proposition",
            "approved_terms": "approved_terms",
            "banned_terms": "banned_terms",
            "compliance_notes": "compliance_notes",
            "brand_values": "brand_values",
            "example_good": "example_good",
            "example_bad": "example_bad",
            "is_default": "is_default",
        }
        for attr in ["name", "positioning", "voice", "metadata", *alias_map.keys()]:
            val = getattr(body, attr, None)
            if val is not None:
                payload[attr] = val

        if not payload:
            raise HTTPException(status_code=400, detail="No fields to update.")

        row = repo.update_profile(profile_id, payload)
        logger.info("Brand profile updated id=%s", profile_id)
        return row
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Brand profile update failed profile_id=%s", profile_id)
        raise HTTPException(status_code=500, detail=f"Brand profile update failed: {error}") from error


@app.post("/brand/score")
def brand_score(body: BrandScoreBody) -> dict[str, Any]:
    logger.info("Received /brand/score request profile_id=%s content_chars=%s", body.brand_profile_id, len(body.content))
    try:
        ctx = retrieve_brand_context(topic=body.topic, profile_id=body.brand_profile_id)
        if ctx is None:
            raise HTTPException(status_code=404, detail=f"Brand profile '{body.brand_profile_id}' not found.")
        score: BrandConsistencyScore = score_brand_consistency(body.content, ctx)
        logger.info(
            "/brand/score completed profile_id=%s overall=%.1f verdict=%s",
            body.brand_profile_id, score.overall_score, score.verdict,
        )
        return {
            "overallScore": score.overall_score,
            "voiceScore": score.voice_score,
            "terminologyScore": score.terminology_score,
            "audienceScore": score.audience_score,
            "violations": score.violations,
            "suggestions": score.suggestions,
            "verdict": score.verdict,
        }
    except HTTPException:
        raise
    except ContentGeneratorError as error:
        logger.error("Brand scoring generation error: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception as error:
        logger.exception("Brand scoring unexpected error")
        raise HTTPException(status_code=500, detail=f"Unexpected scoring error: {error}") from error


@app.post("/compare")
def compare(body: ContentArtifactBody) -> dict[str, Any]:
    logger.info("Received /compare request topic='%s' content_chars=%s", body.topic, len(body.content))
    comparison = compare_uniqueness(body.content)
    logger.info(
        "Comparison completed topic='%s' unique_terms=%s compared_words=%s",
        body.topic,
        comparison.unique_term_count,
        comparison.compared_word_count,
    )
    return {
        "baseline": comparison.baseline,
        "uniqueTerms": comparison.unique_terms,
        "uniqueTermCount": comparison.unique_term_count,
        "comparedWordCount": comparison.compared_word_count,
    }


@app.post("/export/docx")
def export_docx(body: ContentArtifactBody) -> Response:
    logger.info("Received /export/docx request topic='%s' content_chars=%s", body.topic, len(body.content))
    try:
        docx_bytes = make_docx_bytes(body.content, body.topic)
    except ModuleNotFoundError as error:
        logger.error("DOCX export unavailable: python-docx is not installed")
        raise HTTPException(
            status_code=503,
            detail="DOCX export requires python-docx. Install dependencies with pip install -r requirements.txt.",
        ) from error

    safe_filename = safe_download_filename(body.topic)
    logger.info("DOCX export completed filename=%s.docx bytes=%s", safe_filename, len(docx_bytes))
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}.docx"'},
    )


@app.post("/chat")
def chat(body: ChatBody) -> dict[str, str]:
    logger.info("Received /chat request messages=%s", len(body.messages))
    try:
        generator = ContentGenerator()
        content = generator.generate_content(build_chat_prompt(body.messages))
        logger.info("/chat completed response_chars=%s", len(content))
        return {"content": content}
    except ValueError as error:
        logger.error("Chat validation failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ContentGeneratorError as error:
        logger.error("Chat generation failed: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/chat/stream")
async def chat_stream(body: ChatBody) -> StreamingResponse:
    logger.info("Received /chat/stream request messages=%s", len(body.messages))
    try:
        generator = ContentGenerator()
        content = generator.generate_content(build_chat_prompt(body.messages))
        logger.info("/chat/stream generated response_chars=%s", len(content))
    except ValueError as error:
        logger.error("Chat stream validation failed: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ContentGeneratorError as error:
        logger.error("Chat stream generation failed: %s", error)
        raise HTTPException(status_code=502, detail=str(error)) from error

    async def stream() -> AsyncIterator[str]:
        for token in content.split(" "):
            yield token + " "

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")
