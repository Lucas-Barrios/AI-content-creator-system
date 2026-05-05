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
from fastapi import FastAPI, File, HTTPException, UploadFile
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
    )


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
