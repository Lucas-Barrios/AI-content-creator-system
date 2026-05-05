# Database and Vector Store Design

This schema is designed for a multi-tenant AI marketing content product for SMEs.

## Tenant Model

- `organizations`: SaaS customer workspace. For an agency, this can represent the agency account.
- `organization_members`: user membership and role inside an organization.
- `clients`: SME brands/customers managed inside an organization.
- `projects`: campaign or ongoing content workspaces inside a client.

Every business table stores `organization_id`, and most content tables also store `client_id` and `project_id`.
This denormalization is intentional: it keeps row-level security simple, makes filtering fast, and prevents accidental cross-client retrieval.

## Core Tables

- `profiles`: Supabase Auth user profiles.
- `brand_profiles`: brand memory, tone, positioning, audience, approved terms, banned terms, and compliance notes.
- `uploaded_documents`: uploaded source files and document-level metadata.
- `document_chunks`: searchable text chunks with metadata for retrieval filtering.
- `document_embeddings`: pgvector embeddings for chunks.
- `content_briefs`: structured briefs created before generation.
- `generated_outputs`: saved generated content and repurposed variants.
- `campaigns`: campaign-level planning object.
- `campaign_items`: assets planned inside a campaign.
- `content_calendar_items`: scheduled or planned content posts.
- `feedback_events`: reviewer approval/revision decisions.
- `output_versions`: edit history and generated-output revisions.

## Retrieval Metadata

RAG retrieval should filter by:

- `client_id`
- `project_id`
- `content_type`
- `language`
- `channel`
- optional `tags`
- optional `source_kind`
- optional JSON metadata

The most important retrieval fields are present on both `uploaded_documents` and `document_chunks`.
The query function joins `document_embeddings`, `document_chunks`, and `uploaded_documents`.

## Vector Store

The migration enables Supabase `pgvector` in the `extensions` schema and uses:

- model: `text-embedding-3-small`
- dimensions: `1536`
- column: `document_embeddings.embedding extensions.vector(1536)`
- index: HNSW with cosine distance

The included `match_document_chunks(...)` function returns tenant-scoped chunks sorted by cosine similarity.
It supports filters for client, project, content type, language, and channel.

## Row-Level Security

RLS is enabled on every public table.

Access rule:

- Users can read rows if they belong to the owning organization.
- Owners/admins/editors can create and manage most content records.
- Viewers can read but not mutate content.
- Backend ingestion and embedding jobs should use the Supabase service role key from the server only.

Never expose the service role key in the frontend.

## To Be

- Add Supabase Storage bucket policies for uploaded documents and brand assets.
- Add Edge Function or backend worker for document parsing and embedding jobs.
- Add usage and billing tables once SaaS packaging is defined.
- Add prompt versioning and evaluation score tables when prompt experiments begin.
- Consider hybrid search by adding `tsvector` fields to `document_chunks` if keyword precision becomes important.
