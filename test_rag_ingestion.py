"""Tests for the RAG ingestion pipeline.

Run:
  python3 test_rag_ingestion.py
"""

from __future__ import annotations

from uuid import uuid4

from src.rag_ingestion import (
    KnowledgeSourceInput,
    RagIngestionService,
    TextChunk,
    chunk_text,
    clean_text,
    extract_text_from_source,
    hash_text,
)


class FakeEmbedder:
    model = "fake-embedding-model"
    dimensions = 3

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), float(len(text)), 1.0] for index, text in enumerate(texts)]


class InMemoryKnowledgeRepository:
    def __init__(self) -> None:
        self.documents: list[dict] = []
        self.chunks: list[dict] = []
        self.embeddings: list[dict] = []

    def find_document_by_hash(self, client_id: str, project_id: str | None, content_hash: str) -> dict | None:
        for document in self.documents:
            if (
                document["client_id"] == client_id
                and document["project_id"] == project_id
                and document["content_hash"] == content_hash
            ):
                return document
        return None

    def create_document(self, source: KnowledgeSourceInput, text: str, content_hash: str) -> dict:
        document = {
            "id": str(uuid4()),
            "organization_id": source.organization_id,
            "client_id": source.client_id,
            "project_id": source.project_id,
            "title": source.title,
            "status": "processing",
            "content_hash": content_hash,
        }
        self.documents.append(document)
        return document

    def mark_document_status(self, document_id: str, status: str, error_message: str | None = None) -> None:
        for document in self.documents:
            if document["id"] == document_id:
                document["status"] = status
                document["error_message"] = error_message

    def create_chunk(self, source: KnowledgeSourceInput, document_id: str, chunk: TextChunk) -> dict:
        record = {
            "id": str(uuid4()),
            "document_id": document_id,
            "content": chunk.content,
            "chunk_hash": chunk.chunk_hash,
            "chunk_index": chunk.index,
        }
        self.chunks.append(record)
        return record

    def create_embedding(
        self,
        source: KnowledgeSourceInput,
        document_id: str,
        chunk_id: str,
        embedding: list[float],
        model: str,
        dimensions: int,
    ) -> dict:
        record = {
            "id": str(uuid4()),
            "document_id": document_id,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "embedding_model": model,
            "embedding_dimensions": dimensions,
        }
        self.embeddings.append(record)
        return record


def make_source(text: str) -> KnowledgeSourceInput:
    return KnowledgeSourceInput(
        organization_id=str(uuid4()),
        client_id=str(uuid4()),
        project_id=str(uuid4()),
        title="Brand guidelines",
        text=text,
        source_kind="brand",
        content_type="blog",
        language="english",
        channel="blog",
        tags=["brand", "voice"],
    )


def test_text_extraction_and_cleaning() -> None:
    source = make_source("  First line.  \n\n\n Second    line. ")
    assert extract_text_from_source(source).startswith("  First")
    assert clean_text(source.text or "") == "First line.\n\nSecond line."


def test_txt_file_extraction() -> None:
    source = KnowledgeSourceInput(
        organization_id=str(uuid4()),
        client_id=str(uuid4()),
        project_id=None,
        title="Copy",
        file_bytes=b"Hello from a text file.",
        filename="copy.txt",
        mime_type="text/plain",
    )
    assert extract_text_from_source(source) == "Hello from a text file."


def test_chunking_has_hashes_and_overlap() -> None:
    text = "\n\n".join(f"Paragraph {index} with useful marketing context for SMEs." for index in range(40))
    chunks = chunk_text(text, max_tokens=80, overlap_tokens=20)
    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert chunks[0].chunk_hash == hash_text(chunks[0].content)
    assert all(chunk.token_count > 0 for chunk in chunks)


def test_ingestion_stores_document_chunks_and_embeddings() -> None:
    repository = InMemoryKnowledgeRepository()
    service = RagIngestionService(repository=repository, embedder=FakeEmbedder())
    result = service.ingest(make_source("This brand helps SMEs create better marketing content faster. " * 80))

    assert result.status == "ready"
    assert not result.duplicate
    assert result.chunk_count == len(repository.chunks)
    assert result.embedding_count == len(repository.embeddings)
    assert repository.documents[0]["status"] == "ready"


def test_duplicate_detection_reuses_existing_document() -> None:
    repository = InMemoryKnowledgeRepository()
    service = RagIngestionService(repository=repository, embedder=FakeEmbedder())
    source = make_source("Existing marketing copy with enough detail for ingestion. " * 40)

    first = service.ingest(source)
    second = service.ingest(source)

    assert not first.duplicate
    assert second.duplicate
    assert second.document_id == first.document_id
    assert len(repository.documents) == 1


def main() -> None:
    test_text_extraction_and_cleaning()
    test_txt_file_extraction()
    test_chunking_has_hashes_and_overlap()
    test_ingestion_stores_document_chunks_and_embeddings()
    test_duplicate_detection_reuses_existing_document()
    print("rag ingestion tests passed")


if __name__ == "__main__":
    main()
