-- AI Marketing Content OS schema for Supabase Postgres + pgvector.
--
-- Tenant model:
--   organizations = SaaS customer/workspace owner
--   clients       = SME/customer brands managed inside an organization
--   projects      = campaign/content workspaces inside a client
--
-- RLS model:
--   Users can access rows only when they are members of the owning organization.
--   Service-role backend jobs can bypass RLS for ingestion, embedding, and automation.

create extension if not exists pgcrypto;
create extension if not exists vector with schema extensions;

create type public.member_role as enum ('owner', 'admin', 'editor', 'viewer');
create type public.client_status as enum ('active', 'archived');
create type public.project_status as enum ('active', 'paused', 'completed', 'archived');
create type public.source_status as enum ('uploaded', 'processing', 'ready', 'failed', 'archived');
create type public.source_kind as enum ('brand', 'product', 'audience', 'market', 'competitor', 'campaign', 'policy', 'other');
create type public.content_type as enum ('blog', 'social', 'email', 'newsletter', 'ad', 'landing_page', 'program', 'other');
create type public.content_channel as enum ('website', 'linkedin', 'instagram', 'facebook', 'x', 'email', 'newsletter', 'ads', 'blog', 'other');
create type public.output_status as enum ('draft', 'approved', 'needs_revision', 'scheduled', 'published', 'archived');
create type public.feedback_status as enum ('approved', 'needs_revision', 'rejected');

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  plan text not null default 'free',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.organization_members (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.member_role not null default 'viewer',
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create table public.clients (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  slug text not null,
  industry text,
  website_url text,
  status public.client_status not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, slug)
);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  name text not null,
  slug text not null,
  objective text,
  default_language text not null default 'english',
  status public.project_status not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (client_id, slug),
  constraint projects_same_organization check (organization_id is not null)
);

create table public.brand_profiles (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  name text not null default 'Default brand profile',
  positioning text,
  voice text,
  tone_guidelines text,
  audience_summary text,
  approved_terms text[] not null default '{}',
  banned_terms text[] not null default '{}',
  compliance_notes text,
  brand_values text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  is_default boolean not null default false,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.uploaded_documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  uploaded_by uuid references auth.users(id) on delete set null,
  title text not null,
  original_filename text not null,
  storage_bucket text,
  storage_path text,
  mime_type text,
  file_size_bytes bigint,
  content_hash text,
  source_kind public.source_kind not null default 'other',
  status public.source_status not null default 'uploaded',
  language text,
  content_type public.content_type,
  channel public.content_channel,
  tags text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  document_id uuid not null references public.uploaded_documents(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  chunk_hash text not null,
  token_count integer,
  source_kind public.source_kind not null default 'other',
  language text,
  content_type public.content_type,
  channel public.content_channel,
  tags text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create table public.document_embeddings (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  document_id uuid not null references public.uploaded_documents(id) on delete cascade,
  chunk_id uuid not null unique references public.document_chunks(id) on delete cascade,
  embedding_model text not null default 'text-embedding-3-small',
  embedding_dimensions integer not null default 1536,
  embedding extensions.vector(1536) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.content_briefs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  brand_profile_id uuid references public.brand_profiles(id) on delete set null,
  title text not null,
  objective text,
  audience text,
  language text not null default 'english',
  content_type public.content_type not null,
  channel public.content_channel,
  brief text not null,
  retrieval_query text,
  retrieved_chunk_ids uuid[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.campaigns (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  name text not null,
  objective text,
  audience text,
  start_date date,
  end_date date,
  status public.project_status not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.generated_outputs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete set null,
  brief_id uuid references public.content_briefs(id) on delete set null,
  brand_profile_id uuid references public.brand_profiles(id) on delete set null,
  parent_output_id uuid references public.generated_outputs(id) on delete set null,
  title text,
  prompt text,
  content text not null,
  content_type public.content_type not null,
  channel public.content_channel,
  language text not null default 'english',
  status public.output_status not null default 'draft',
  model text,
  word_count integer,
  retrieved_chunk_ids uuid[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.campaign_items (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  campaign_id uuid not null references public.campaigns(id) on delete cascade,
  output_id uuid references public.generated_outputs(id) on delete set null,
  title text not null,
  content_type public.content_type not null,
  channel public.content_channel,
  status public.output_status not null default 'draft',
  due_date date,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.content_calendar_items (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete set null,
  campaign_item_id uuid references public.campaign_items(id) on delete set null,
  output_id uuid references public.generated_outputs(id) on delete set null,
  title text not null,
  channel public.content_channel not null,
  content_type public.content_type not null,
  language text not null default 'english',
  scheduled_for timestamptz,
  status public.output_status not null default 'draft',
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.feedback_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  output_id uuid not null references public.generated_outputs(id) on delete cascade,
  status public.feedback_status not null,
  comment text,
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table public.output_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  client_id uuid not null references public.clients(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  output_id uuid not null references public.generated_outputs(id) on delete cascade,
  version_number integer not null,
  content text not null,
  change_summary text,
  edited_by uuid references auth.users(id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (output_id, version_number)
);

create index profiles_updated_at_idx on public.profiles (updated_at desc);
create index organization_members_user_id_idx on public.organization_members (user_id);
create index clients_organization_id_idx on public.clients (organization_id);
create index projects_client_id_idx on public.projects (client_id);
create index brand_profiles_client_project_idx on public.brand_profiles (client_id, project_id);
create index uploaded_documents_retrieval_filter_idx on public.uploaded_documents (client_id, project_id, content_type, language, channel);
create unique index uploaded_documents_content_hash_idx
  on public.uploaded_documents (client_id, coalesce(project_id, '00000000-0000-0000-0000-000000000000'::uuid), content_hash)
  where content_hash is not null;
create index uploaded_documents_tags_idx on public.uploaded_documents using gin (tags);
create index document_chunks_retrieval_filter_idx on public.document_chunks (client_id, project_id, content_type, language, channel);
create unique index document_chunks_hash_idx on public.document_chunks (document_id, chunk_hash);
create index document_chunks_tags_idx on public.document_chunks using gin (tags);
create index document_chunks_metadata_idx on public.document_chunks using gin (metadata);
create index document_embeddings_tenant_idx on public.document_embeddings (organization_id, client_id, project_id);
create index document_embeddings_embedding_hnsw_idx
  on public.document_embeddings
  using hnsw (embedding extensions.vector_cosine_ops);
create index content_briefs_project_idx on public.content_briefs (project_id, created_at desc);
create index campaigns_project_idx on public.campaigns (project_id, created_at desc);
create index generated_outputs_project_idx on public.generated_outputs (project_id, created_at desc);
create index generated_outputs_filter_idx on public.generated_outputs (client_id, project_id, content_type, language, channel, status);
create index campaign_items_campaign_idx on public.campaign_items (campaign_id, due_date);
create index calendar_project_schedule_idx on public.content_calendar_items (project_id, scheduled_for);
create index calendar_filter_idx on public.content_calendar_items (client_id, project_id, channel, content_type, status);
create index feedback_events_output_idx on public.feedback_events (output_id, created_at desc);
create index output_versions_output_idx on public.output_versions (output_id, version_number desc);

create trigger profiles_set_updated_at before update on public.profiles for each row execute function public.set_updated_at();
create trigger organizations_set_updated_at before update on public.organizations for each row execute function public.set_updated_at();
create trigger clients_set_updated_at before update on public.clients for each row execute function public.set_updated_at();
create trigger projects_set_updated_at before update on public.projects for each row execute function public.set_updated_at();
create trigger brand_profiles_set_updated_at before update on public.brand_profiles for each row execute function public.set_updated_at();
create trigger uploaded_documents_set_updated_at before update on public.uploaded_documents for each row execute function public.set_updated_at();
create trigger document_embeddings_set_updated_at before update on public.document_embeddings for each row execute function public.set_updated_at();
create trigger content_briefs_set_updated_at before update on public.content_briefs for each row execute function public.set_updated_at();
create trigger campaigns_set_updated_at before update on public.campaigns for each row execute function public.set_updated_at();
create trigger generated_outputs_set_updated_at before update on public.generated_outputs for each row execute function public.set_updated_at();
create trigger campaign_items_set_updated_at before update on public.campaign_items for each row execute function public.set_updated_at();
create trigger content_calendar_items_set_updated_at before update on public.content_calendar_items for each row execute function public.set_updated_at();

create or replace function public.is_organization_member(target_organization_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.organization_members om
    where om.organization_id = target_organization_id
      and om.user_id = auth.uid()
  );
$$;

create or replace function public.has_organization_role(target_organization_id uuid, allowed_roles public.member_role[])
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.organization_members om
    where om.organization_id = target_organization_id
      and om.user_id = auth.uid()
      and om.role = any(allowed_roles)
  );
$$;

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
  where public.is_organization_member(dc.organization_id)
    and (filter_client_id is null or dc.client_id = filter_client_id)
    and (filter_project_id is null or dc.project_id = filter_project_id)
    and (filter_content_type is null or dc.content_type = filter_content_type)
    and (filter_language is null or dc.language = filter_language)
    and (filter_channel is null or dc.channel = filter_channel)
    and 1 - (de.embedding <=> query_embedding) >= match_threshold
  order by de.embedding <=> query_embedding
  limit least(match_count, 30);
$$;

alter table public.profiles enable row level security;
alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.clients enable row level security;
alter table public.projects enable row level security;
alter table public.brand_profiles enable row level security;
alter table public.uploaded_documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.document_embeddings enable row level security;
alter table public.content_briefs enable row level security;
alter table public.campaigns enable row level security;
alter table public.generated_outputs enable row level security;
alter table public.campaign_items enable row level security;
alter table public.content_calendar_items enable row level security;
alter table public.feedback_events enable row level security;
alter table public.output_versions enable row level security;

create policy "Users can view their own profile" on public.profiles
  for select using (id = auth.uid());
create policy "Users can update their own profile" on public.profiles
  for update using (id = auth.uid()) with check (id = auth.uid());
create policy "Users can insert their own profile" on public.profiles
  for insert with check (id = auth.uid());

create policy "Members can view organizations" on public.organizations
  for select using (public.is_organization_member(id));
create policy "Admins can update organizations" on public.organizations
  for update using (public.has_organization_role(id, array['owner','admin']::public.member_role[]))
  with check (public.has_organization_role(id, array['owner','admin']::public.member_role[]));

create policy "Members can view organization memberships" on public.organization_members
  for select using (public.is_organization_member(organization_id));
create policy "Owners and admins can manage memberships" on public.organization_members
  for all using (public.has_organization_role(organization_id, array['owner','admin']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin']::public.member_role[]));

create policy "Members can view clients" on public.clients
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage clients" on public.clients
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view projects" on public.projects
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage projects" on public.projects
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view brand profiles" on public.brand_profiles
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage brand profiles" on public.brand_profiles
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view uploaded documents" on public.uploaded_documents
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage uploaded documents" on public.uploaded_documents
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view document chunks" on public.document_chunks
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage document chunks" on public.document_chunks
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view document embeddings" on public.document_embeddings
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage document embeddings" on public.document_embeddings
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view content briefs" on public.content_briefs
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage content briefs" on public.content_briefs
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view campaigns" on public.campaigns
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage campaigns" on public.campaigns
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view generated outputs" on public.generated_outputs
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage generated outputs" on public.generated_outputs
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view campaign items" on public.campaign_items
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage campaign items" on public.campaign_items
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view calendar items" on public.content_calendar_items
  for select using (public.is_organization_member(organization_id));
create policy "Editors can manage calendar items" on public.content_calendar_items
  for all using (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]))
  with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view feedback events" on public.feedback_events
  for select using (public.is_organization_member(organization_id));
create policy "Editors can create feedback events" on public.feedback_events
  for insert with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));

create policy "Members can view output versions" on public.output_versions
  for select using (public.is_organization_member(organization_id));
create policy "Editors can create output versions" on public.output_versions
  for insert with check (public.has_organization_role(organization_id, array['owner','admin','editor']::public.member_role[]));
