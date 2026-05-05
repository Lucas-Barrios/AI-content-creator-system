-- Seed the three demo tenant rows that the frontend hard-codes, and fix
-- match_document_chunks so the service-role backend can actually get results.
--
-- Run this once in the Supabase SQL editor (or via supabase db push) after the
-- main schema migration has been applied.

-- ── 1. Demo tenant rows ────────────────────────────────────────────────────────
-- UUIDs must match defaultWorkspace in frontend/lib/workspace.ts

insert into public.organizations (id, name, slug, plan)
values ('00000000-0000-0000-0000-000000000001', 'Demo Organization', 'demo-org', 'pro')
on conflict (id) do nothing;

insert into public.clients (id, organization_id, name, slug, industry)
values (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',
  'Demo Client',
  'demo-client',
  'Education'
)
on conflict (id) do nothing;

insert into public.projects (id, organization_id, client_id, name, slug, objective, default_language)
values (
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002',
  'Marketing Workspace',
  'marketing-workspace',
  'General marketing content production',
  'english'
)
on conflict (id) do nothing;


-- ── 2. Fix match_document_chunks for service-role callers ──────────────────────
-- The original WHERE clause calls is_organization_member(org_id), which checks
-- auth.uid(). When the Python backend uses the service-role key, auth.uid() is
-- NULL, so the function always returns zero rows.
--
-- Fix: allow the query when the caller holds the service_role JWT claim, so the
-- backend RAG pipeline can retrieve chunks without needing a logged-in user.

create or replace function public.match_document_chunks(
  query_embedding extensions.vector(1536),
  match_count integer default 8,
  match_threshold double precision default 0.72,
  filter_client_id uuid default null,
  filter_project_id uuid default null,
  filter_content_type public.content_type default null,
  filter_language text default null,
  filter_channel public.content_channel default null
)
returns table (
  chunk_id uuid,
  document_id uuid,
  client_id uuid,
  project_id uuid,
  title text,
  content text,
  source_kind public.source_kind,
  content_type public.content_type,
  language text,
  channel public.content_channel,
  tags text[],
  similarity double precision
)
language sql
stable
as $$
  select
    dc.id as chunk_id,
    dc.document_id,
    dc.client_id,
    dc.project_id,
    ud.title,
    dc.content,
    dc.source_kind,
    dc.content_type,
    dc.language,
    dc.channel,
    dc.tags,
    1 - (de.embedding <=> query_embedding) as similarity
  from public.document_embeddings de
  join public.document_chunks dc on dc.id = de.chunk_id
  join public.uploaded_documents ud on ud.id = dc.document_id
  where
    -- service-role backend bypasses user-auth check; authenticated users go
    -- through the organisation-membership gate
    (
      coalesce(current_setting('request.jwt.claims', true)::jsonb->>'role', '') = 'service_role'
      or public.is_organization_member(dc.organization_id)
    )
    and (filter_client_id  is null or dc.client_id    = filter_client_id)
    and (filter_project_id is null or dc.project_id   = filter_project_id)
    and (filter_content_type is null or dc.content_type = filter_content_type)
    and (filter_language   is null or dc.language     = filter_language)
    and (filter_channel    is null or dc.channel      = filter_channel)
    and 1 - (de.embedding <=> query_embedding) >= match_threshold
  order by de.embedding <=> query_embedding
  limit least(match_count, 30);
$$;
