# RAG Ingestion Pipeline

The backend now supports UI-agnostic knowledge ingestion for client/project marketing sources.

## Supported Sources

- PDF uploads
- DOCX uploads
- TXT uploads
- Markdown uploads
- Website text pasted manually
- Existing marketing copy pasted manually

## Pipeline

1. Validate tenant metadata.
2. Extract text from upload or pasted text.
3. Clean whitespace and paragraph boundaries.
4. Chunk text by paragraphs, with word overlap for continuity.
5. Generate OpenAI embeddings with `text-embedding-3-small`.
6. Store document metadata in `uploaded_documents`.
7. Store chunks in `document_chunks`.
8. Store vectors in `document_embeddings`.
9. Mark the document `ready`, `failed`, or return an existing duplicate.

## Endpoints

### Pasted Text

`POST /knowledge/ingest-text`

```json
{
  "organizationId": "00000000-0000-0000-0000-000000000001",
  "clientId": "00000000-0000-0000-0000-000000000002",
  "projectId": "00000000-0000-0000-0000-000000000003",
  "title": "Website homepage copy",
  "text": "Paste source text here...",
  "sourceKind": "brand",
  "contentType": "blog",
  "language": "english",
  "channel": "website",
  "tags": ["homepage", "brand"]
}
```

Response:

```json
{
  "documentId": "generated-document-id",
  "duplicate": false,
  "contentHash": "sha256-hash",
  "chunkCount": 4,
  "embeddingCount": 4,
  "status": "ready",
  "message": "Knowledge source ingested successfully."
}
```

### File Upload

`POST /knowledge/ingest-file`

Multipart form fields:

- `organizationId`
- `clientId`
- `projectId`
- `title`
- `sourceKind`
- `contentType`
- `language`
- `channel`
- `tags` as comma-separated text
- `file`

### Retrieval

`POST /knowledge/search`

```json
{
  "query": "brand voice and proof points for SME marketing",
  "clientId": "00000000-0000-0000-0000-000000000002",
  "projectId": "00000000-0000-0000-0000-000000000003",
  "contentType": "blog",
  "language": "english",
  "channel": "blog",
  "matchCount": 8,
  "matchThreshold": 0.72
}
```

Response:

```json
{
  "matches": [
    {
      "chunk_id": "chunk-id",
      "document_id": "document-id",
      "client_id": "client-id",
      "project_id": "project-id",
      "title": "Website homepage copy",
      "content": "Relevant chunk text...",
      "source_kind": "brand",
      "content_type": "blog",
      "language": "english",
      "channel": "blog",
      "tags": ["homepage", "brand"],
      "similarity": 0.84
    }
  ],
  "count": 1
}
```

## Duplicate Detection

The cleaned full document text is hashed with SHA-256. A duplicate is detected when the same `client_id`, `project_id`, and `content_hash` already exist.

## Environment

Required backend variables:

```bash
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

`SUPABASE_SERVICE_ROLE_KEY` must only be used server-side.
