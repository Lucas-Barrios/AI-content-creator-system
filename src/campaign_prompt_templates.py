"""
campaign_prompt_templates.py

Prompt library for the Campaign Generator feature.

Two-stage architecture:
  Stage 1 — concept_prompt()       : returns full campaign strategy as JSON
  Stage 2 — asset_prompt(channel)  : generates one polished asset per channel

All prompts are brand-context-aware: they accept an optional brand_block
string (from brand_intelligence.assemble_brand_block) that is injected before
content instructions so the model reads brand rules first.
"""

from __future__ import annotations

# ── Stage 1: Campaign Concept ─────────────────────────────────────────────────

_CONCEPT_SCHEMA = """\
Return ONLY valid JSON — no markdown fences, no extra text.

Required schema:
{
  "name": "<short campaign name, max 8 words>",
  "concept_summary": "<1-2 sentence campaign concept>",
  "core_message": "<the single sentence that every asset must communicate>",
  "audience_angle": "<how to frame the message specifically for this audience>",
  "channel_strategy": "<how each selected channel plays a distinct role>",
  "content_ideas": [
    {
      "id": 1,
      "title": "<content piece title>",
      "channel": "<one of: linkedin | instagram | email | blog | ads>",
      "format": "<e.g. carousel | article | story | newsletter | search ad>",
      "hook": "<opening line or visual concept>",
      "week": <1–4 integer>
    }
  ],
  "cta_suggestions": ["<CTA text>", "<CTA text>", "<CTA text>"],
  "calendar_draft": [
    {
      "week": <1–4>,
      "day": "<Mon | Tue | Wed | Thu | Fri>",
      "channel": "<channel>",
      "title": "<content title>",
      "content_type": "<post | story | email | article | ad>"
    }
  ]
}

Rules:
- content_ideas: produce 6–10 ideas spread across the selected channels.
- calendar_draft: produce one entry per content idea, spread over the campaign period.
- cta_suggestions: 3–5 options, each under 8 words.
- Do NOT invent facts. Ground claims in the knowledge base context.
- If brand intelligence is provided, every idea must respect the brand voice and avoid banned terms.\
"""


def concept_prompt(
    goal: str,
    offer: str,
    audience: str,
    channels: list[str],
    start_date: str,
    end_date: str,
    language: str,
    tone: str,
    kb_context: str,
    brand_block: str = "",
) -> str:
    channels_str = ", ".join(channels) if channels else "linkedin, instagram, email"
    lang_instruction = (
        "Write all text in German (formal Sie)."
        if language.lower() == "german"
        else "Write all text in British English."
    )
    return f"""\
You are a senior marketing strategist building a complete campaign plan for an SME.
Your output will be consumed by an automated system — return ONLY the JSON schema below.

{_CONCEPT_SCHEMA}

{brand_block}
--- KNOWLEDGE BASE CONTEXT ---
{kb_context or "(no additional context provided)"}
--- END CONTEXT ---

CAMPAIGN BRIEF:
  Goal           : {goal}
  Offer/Service  : {offer}
  Target Audience: {audience}
  Channels       : {channels_str}
  Campaign Period: {start_date} to {end_date}
  Tone           : {tone}
  Language       : {lang_instruction}

Generate the campaign concept JSON now:\
"""


# ── Stage 2: Per-Channel Asset Prompts ────────────────────────────────────────

def _common_header(concept: dict, brand_block: str, language: str) -> str:
    lang_note = (
        "Write entirely in German using formal Sie address."
        if language.lower() == "german"
        else "Write in British English."
    )
    return f"""\
{brand_block}
CAMPAIGN CONTEXT:
  Name          : {concept.get("name", "")}
  Core Message  : {concept.get("core_message", "")}
  Audience Angle: {concept.get("audience_angle", "")}
  Primary CTAs  : {", ".join(concept.get("cta_suggestions", [])[:3])}
  Language      : {lang_note}

RULES: Ground every claim in the campaign context. Never invent statistics or credentials.
If brand intelligence is present, honour all voice, terminology, and compliance rules.\
"""


def linkedin_post_prompt(
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    header = _common_header(concept, brand_block, language)
    return f"""\
You are a B2B LinkedIn content specialist.
Write a single LinkedIn post for the campaign below.

{header}

{"ADDITIONAL CONTEXT:\\n" + extra_context if extra_context else ""}

OUTPUT REQUIREMENTS:
- Length: 120–180 words.
- Structure: Hook (1 sentence) → 3 short body paragraphs → CTA.
- Hook: must be a concrete fact, outcome, or counterintuitive claim — NOT "Excited to share..."
- Include 4–6 relevant hashtags on the final line.
- Format as plain text (no markdown headers).
- Return ONLY the post text.\
"""


def instagram_caption_prompt(
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    header = _common_header(concept, brand_block, language)
    return f"""\
You are an Instagram content strategist.
Write a single Instagram caption for the campaign below.

{header}

{"ADDITIONAL CONTEXT:\\n" + extra_context if extra_context else ""}

OUTPUT REQUIREMENTS:
- Length: 60–90 words.
- First line: punchy visual hook that works without seeing the image.
- Use 1–2 emojis maximum — no spam.
- End with a clear CTA (e.g. "Link in bio →").
- Include 8–12 niche hashtags on a separate line.
- Return ONLY the caption text.\
"""


def email_copy_prompt(
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    header = _common_header(concept, brand_block, language)
    return f"""\
You are an email marketing specialist.
Write a complete marketing email for the campaign below.

{header}

{"ADDITIONAL CONTEXT:\\n" + extra_context if extra_context else ""}

OUTPUT FORMAT (use these exact labels, no markdown headers):
SUBJECT: <max 9 words, creates curiosity or states a benefit>
PREVIEW: <max 12 words, shown in inbox before opening>
BODY:
<opening: 2 sentences anchored to a specific fact or outcome, not "We hope this email finds you well">
<section 1: the core offer — what it is and why it matters now (60–80 words)>
<section 2: proof point or social proof (40–60 words)>
<CTA: one clear action sentence + button label in [brackets]>
FOOTER: Unsubscribe | Privacy Policy

Return ONLY the formatted email copy.\
"""


def blog_outline_prompt(
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    header = _common_header(concept, brand_block, language)
    return f"""\
You are a content strategist and SEO writer.
Write a detailed blog post outline for the campaign below.

{header}

{"ADDITIONAL CONTEXT:\\n" + extra_context if extra_context else ""}

OUTPUT FORMAT (use these exact labels):
TITLE: <SEO-optimised title, 55–65 characters>
HOOK: <opening sentence — a specific stat, story, or counterintuitive claim>
META: <meta description, 140–155 characters>
SECTIONS:
1. <Section heading>
   - <key point>
   - <key point>
   - <key point>
2. <Section heading>
   ...
(4–6 sections total)
CTA: <closing call-to-action sentence>
INTERNAL LINKS: <2–3 suggested anchor text phrases for internal linking>

Return ONLY the outline.\
"""


def ad_copy_prompt(
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    header = _common_header(concept, brand_block, language)
    return f"""\
You are a performance marketing copywriter specialising in paid search and social ads.
Write ad copy variants for the campaign below.

{header}

{"ADDITIONAL CONTEXT:\\n" + extra_context if extra_context else ""}

OUTPUT FORMAT (use these exact labels for each variant):
VARIANT A — Search Ad:
  Headline 1: <max 30 chars>
  Headline 2: <max 30 chars>
  Headline 3: <max 30 chars>
  Description: <max 90 chars>

VARIANT B — Social Ad (LinkedIn/Meta):
  Headline: <max 40 chars>
  Primary text: <max 125 chars>
  CTA button: <Learn More | Sign Up | Get Started | Download | Contact Us>

VARIANT C — Retargeting:
  Headline: <max 40 chars>
  Body: <max 90 chars, assumes audience already knows the brand>

Return ONLY the formatted ad copy.\
"""


# ── Asset prompt dispatcher ────────────────────────────────────────────────────

CHANNEL_PROMPTS = {
    "linkedin": linkedin_post_prompt,
    "instagram": instagram_caption_prompt,
    "email": email_copy_prompt,
    "blog": blog_outline_prompt,
    "ads": ad_copy_prompt,
}

CHANNEL_CONTENT_TYPES = {
    "linkedin": "social",
    "instagram": "social",
    "email": "email",
    "blog": "blog",
    "ads": "ad",
}

CHANNEL_LABELS = {
    "linkedin": "LinkedIn Post",
    "instagram": "Instagram Caption",
    "email": "Email Copy",
    "blog": "Blog Outline",
    "ads": "Ad Copy",
}


def asset_prompt(
    channel: str,
    concept: dict,
    brand_block: str = "",
    language: str = "english",
    extra_context: str = "",
) -> str:
    """Dispatch to the correct per-channel prompt builder."""
    builder = CHANNEL_PROMPTS.get(channel.lower())
    if builder is None:
        raise ValueError(f"No prompt template for channel '{channel}'. Choose from: {list(CHANNEL_PROMPTS)}")
    return builder(concept, brand_block, language, extra_context)
