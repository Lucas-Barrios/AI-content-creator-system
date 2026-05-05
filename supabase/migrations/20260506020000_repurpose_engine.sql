-- Content Repurposing Engine: lineage index + source-type tracking.
--
-- Design: repurposed outputs reuse generated_outputs with parent_output_id
-- pointing to the source entry. No new table needed — the existing schema
-- already captures the full lineage chain.

-- Fast lookup of all repurposed versions derived from a source
create index if not exists generated_outputs_parent_id_idx
  on public.generated_outputs (parent_output_id)
  where parent_output_id is not null;

-- Fast lookup of repurpose sources (entries that are not themselves derived)
create index if not exists generated_outputs_repurpose_source_idx
  on public.generated_outputs (client_id, project_id, created_at desc)
  where parent_output_id is null;

comment on column public.generated_outputs.parent_output_id is
  'For repurposed content: FK to the source generated_output this was derived from. '
  'NULL for original (non-derived) outputs.';
