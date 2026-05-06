# TypeScript Prompt Framework Generation Migration

The new TypeScript prompt framework is now wired into real generation through the Next.js `/api/generate` route while keeping the Python backend as the default rollback path.

## Feature Flags

Set these in `frontend/.env.local`:

```env
ENABLE_TS_PROMPT_FRAMEWORK=false
TS_PROMPT_FRAMEWORK_MODE=social_only
TS_PROMPT_AB_TEST=false
```

Behavior:

- `ENABLE_TS_PROMPT_FRAMEWORK=false`
  Uses the legacy Python `/generate` endpoint.
- `ENABLE_TS_PROMPT_FRAMEWORK=true`
  Routes supported content types through the TypeScript prompt framework.
- `TS_PROMPT_FRAMEWORK_MODE=social_only`
  Only routes `social` / `social_post` through the new framework.
- `TS_PROMPT_FRAMEWORK_MODE=supported`
  Routes `social`, `social_post`, `newsletter`, `email`, `ad`, and `ad_copy`.
- `TS_PROMPT_AB_TEST=true`
  Runs `precision-v1`, `opinionated-v1`, and `evidence-led-v1`, then selects the highest uniqueness score.

Rollback is immediate: set `ENABLE_TS_PROMPT_FRAMEWORK=false` and restart the frontend.

## Flow

1. `POST /api/generate` receives the existing frontend request.
2. `GenerationRouter` decides between legacy Python and the TypeScript framework.
3. Supported TypeScript flow:
   - load brand profile if `clientId` is present
   - retrieve RAG chunks if `clientId` is present
   - build a versioned structured prompt
   - call Python `/llm/generate` for the actual model call
   - generate a generic baseline
   - evaluate uniqueness
   - save to `generated_outputs` through Python `/generated-outputs`
4. Any TypeScript framework error falls back to legacy Python and adds:

```json
{
  "framework": "legacy-python",
  "fallbackReason": "ts_prompt_framework_failed"
}
```

## Comparison Mode

Request:

```json
{
  "contentType": "social",
  "topic": "Flexible MBA for working professionals",
  "audience": "Prospective Students",
  "language": "english",
  "tone": "Professional",
  "length": "Medium",
  "knowledgeBase": "hybrid",
  "compareWithLegacy": true
}
```

Response includes:

- `selectedOutput`
- `legacyOutput`
- `newFrameworkOutput`
- `metadata.comparison`

## Prompt Metadata

New framework outputs store:

```json
{
  "framework": "ts-prompt-framework",
  "promptRunId": "...",
  "templateId": "...",
  "templateVersion": "...",
  "variantId": "...",
  "uniquenessScore": 0,
  "baselineSimilarity": 0,
  "lexicalDiversity": 0,
  "sentenceVariation": 0,
  "ragContextUsed": true,
  "brandProfileUsed": true,
  "generatedAt": "ISO_DATE"
}
```

Legacy outputs store:

```json
{
  "framework": "legacy-python",
  "generatedAt": "ISO_DATE"
}
```

Persistence is best-effort. Generation still succeeds if Supabase persistence is unavailable.

## Repurposing Decision

Repurposing is not migrated yet. It already has a two-stage Python pipeline with extraction, per-format adaptation, lineage persistence via `parent_output_id`, and regeneration. To safely migrate it, the TypeScript router needs:

1. a typed extraction schema equivalent to `src/repurpose_prompt_templates.py`
2. lineage-aware save calls for source and derived outputs
3. regeneration support using the stored extraction payload
4. parity tests against the current `src/repurpose_service.py`

Until those are in place, repurposing should remain on the Python path.
