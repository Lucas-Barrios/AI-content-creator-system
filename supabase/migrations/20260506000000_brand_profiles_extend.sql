-- Extend brand_profiles with value_proposition and content examples.
-- These fields complete the Brand Intelligence Layer's voice capture.

alter table public.brand_profiles
  add column if not exists value_proposition text,
  add column if not exists example_good      text[] not null default '{}',
  add column if not exists example_bad       text[] not null default '{}';

comment on column public.brand_profiles.value_proposition is 'Core value proposition statement used to anchor every piece of content.';
comment on column public.brand_profiles.example_good      is 'Verbatim examples of approved, on-brand content.';
comment on column public.brand_profiles.example_bad       is 'Verbatim examples of off-brand content to avoid.';
