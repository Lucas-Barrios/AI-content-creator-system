"""
repurpose_prompt_templates.py

Two-stage prompt library for the Content Repurposing Engine.

Stage 1 — extract_prompt(source_text)
  Extracts the structural meaning of any source content into a strict JSON schema.
  This is the key pass that guarantees every output format preserves original meaning
  rather than hallucinating new facts — each format prompt receives the extraction,
  not just the raw source.

Stage 2 — format_prompt(format, extraction, source_text, brand_block)
  Generates a single polished, platform-specific asset from the extraction.

Supported output formats:
  linkedin      LinkedIn post (120–180 words, professional hook + CTA)
  instagram     Instagram caption (60–90 words + hashtags)
  email         Email newsletter (subject + preview + full body with sections)
  blog_summary  SEO intro paragraph + key takeaways bullet list + meta description
  ad_copy       Three ad variants: search, social (LinkedIn/Meta), retargeting
  landing_page  Landing page section (outcome headline + sub + 3 bullets + CTA)
  video_script  60-second script with HOOK / PROBLEM / SOLUTION / PROOF / CTA + visual notes

Example extraction output (stage 1):
{
  "title": "Why Remote Teams Outperform Office Teams on Deep Work",
  "core_argument": "Uninterrupted focus time is the single biggest predictor of knowledge-worker output, and remote environments structurally provide more of it.",
  "key_points": [
    "Office workers average 2.5 hours of uninterrupted focus per day vs 4.8 for remote workers",
    "Meeting overhead drops 37% when teams shift to async-first communication",
    "Deep work produces 4x more output per hour than shallow work in cognitive tasks"
  ],
  "facts": [
    "2.5 hours: avg daily focus time in open-plan offices (Microsoft WorkLab, 2024)",
    "4.8 hours: avg daily focus time for remote workers (same study)",
    "37% reduction in meeting time with async-first policies"
  ],
  "quotes": ["'The ability to perform deep work is becoming increasingly rare and increasingly valuable.' — Cal Newport"],
  "tone": "authoritative",
  "audience_signals": "Knowledge workers, team leads, and HR leaders evaluating remote work policies",
  "one_sentence_summary": "Remote workers get nearly twice the daily focus time of office workers — and that gap explains most of the productivity difference."
}
"""

from __future__ import annotations

# ── Stage 1: Extraction ────────────────────────────────────────────────────────

_EXTRACT_SCHEMA = """\
Return ONLY valid JSON — no markdown fences, no extra text.

Required schema:
{
  "title": "<inferred or explicit title, max 12 words>",
  "core_argument": "<the central thesis or main point, 1–2 sentences>",
  "key_points": ["<point>", ...],
  "facts": ["<specific fact, stat, or verifiable claim>", ...],
  "quotes": ["<verbatim quote if present in source, else empty array>"],
  "tone": "<one word: authoritative | conversational | educational | urgent | inspirational | analytical>",
  "audience_signals": "<who the original content appears to be written for>",
  "one_sentence_summary": "<the entire piece distilled into one punchy sentence>"
}

Rules:
- key_points: 4–7 points drawn only from the source text — no invention.
- facts: 3–6 facts, include source attribution if present in the text.
- quotes: verbatim only — do not paraphrase as a quote.
- one_sentence_summary: must work as a standalone social hook.\
"""


def extract_prompt(source_text: str, source_type: str = "article") -> str:
    return f"""\
You are a senior content strategist extracting the structural meaning from a piece of content.
Your extraction will be used to repurpose this content across multiple channels.
Accuracy is critical — do not add, invent, or embellish any information.

{_EXTRACT_SCHEMA}

SOURCE TYPE: {source_type.replace("_", " ").title()}

SOURCE CONTENT:
\"\"\"
{source_text}
\"\"\"

Extract now:\
"""


# ── Stage 2: Per-format adaptation ────────────────────────────────────────────

def _format_header(extraction: dict, brand_block: str, language: str) -> str:
    lang_note = (
        "Write entirely in German using formal Sie address."
        if language.lower() == "german"
        else "Write in British English."
    )
    key_points = "\n".join(f"  - {p}" for p in extraction.get("key_points", []))
    facts = "\n".join(f"  - {f}" for f in extraction.get("facts", []))
    quotes = "\n".join(f'  - "{q}"' for q in extraction.get("quotes", []))

    return f"""\
{brand_block}
SOURCE INTELLIGENCE (use ONLY these facts — do not invent):
  Title            : {extraction.get("title", "")}
  Core Argument    : {extraction.get("core_argument", "")}
  Summary          : {extraction.get("one_sentence_summary", "")}
  Original Tone    : {extraction.get("tone", "")}
  Original Audience: {extraction.get("audience_signals", "")}

Key points:
{key_points or "  (none extracted)"}

Facts & stats:
{facts or "  (none extracted)"}

Verbatim quotes:
{quotes or "  (none)"}

Language: {lang_note}
CRITICAL: Every claim must appear in the source intelligence above. Never invent statistics.\
"""


def linkedin_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are a B2B LinkedIn content specialist.
Repurpose the source content below into a single LinkedIn post.

{header}

OUTPUT REQUIREMENTS:
- Length: 120–180 words.
- Structure: Hook → 3 short body paragraphs → CTA.
- Hook (first sentence): a counterintuitive fact, a specific number, or a question — drawn from the key points or facts above. NEVER start with "Excited to share..." or "I recently read...".
- Body: expand 2–3 of the key points with one grounding fact each.
- CTA: one clear action sentence (save this post / share with your team / link in comments).
- Hashtags: 4–6 on the final line.
- Return ONLY the post text.\
"""


def instagram_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are an Instagram content specialist.
Repurpose the source content below into a single Instagram caption.

{header}

OUTPUT REQUIREMENTS:
- Length: 60–90 words (caption text only, excluding hashtags).
- First line: punchy hook that stands alone as a visual caption — imagine it paired with a strong image.
- Body: 2–3 lines translating the core argument into everyday language.
- CTA: "Link in bio →" or "Save this for later."
- Emojis: 1–2 maximum, placed naturally — no spam.
- Hashtags: 8–12 on a separate final line, mix of niche and broad.
- Return ONLY the caption text.\
"""


def email_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are an email marketing specialist.
Repurpose the source content below into a complete marketing email.

{header}

OUTPUT FORMAT (use these exact labels, plain text):
SUBJECT: <max 9 words — creates curiosity or states a concrete benefit>
PREVIEW: <max 12 words — the inbox preview line, complements the subject>

OPENING:
<2–3 sentences. Start with a specific fact or quote from the source — never "We hope this email finds you well." Warm but direct — written for a professional reader who is pressed for time.>

SECTION 1 — The core insight:
<80–100 words. Explain the core argument in plain language. One fact or stat to ground it.>

SECTION 2 — What this means for you:
<60–80 words. Connect the argument to a practical implication for the audience.>

SECTION 3 — Key takeaways:
<Bullet list of 3–4 points drawn from key_points above.>

CTA:
<One action sentence + button label in [square brackets].>

FOOTER: Unsubscribe | Privacy Policy

Return ONLY the formatted email.\
"""


def blog_summary_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are an SEO content writer.
Repurpose the source content below into a blog post summary suitable as an introduction section.

{header}

OUTPUT FORMAT (use these exact labels):
TITLE: <SEO-optimised blog title, 55–65 characters>
INTRO:
<150–200 word introductory paragraph. Open with the most compelling fact or the core argument.
Do NOT use "In today's world..." or "In this post...". Write as if continuing an established conversation.
Include 1–2 facts from the source to establish credibility.>

KEY TAKEAWAYS:
<Bullet list of 4–6 takeaways, each max 20 words, drawn from key_points above.>

META DESCRIPTION:
<140–155 characters. Front-load the main keyword. States the benefit of reading. No clickbait.>

INTERNAL LINK ANCHORS: <2–3 suggested anchor text phrases for related content>

Return ONLY the formatted blog summary.\
"""


def ad_copy_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are a performance marketing copywriter.
Repurpose the source content into three ad copy variants.

{header}

OUTPUT FORMAT (use these exact labels for each variant):

VARIANT A — Search Ad (Google/Bing):
  Headline 1: <max 30 characters>
  Headline 2: <max 30 characters>
  Headline 3: <max 30 characters>
  Description 1: <max 90 characters>
  Description 2: <max 90 characters>

VARIANT B — Social Ad (LinkedIn / Meta):
  Headline: <max 40 characters — lead with the outcome, not the feature>
  Primary text: <max 125 characters — hook + one fact + implicit CTA>
  CTA button: <Learn More | Download | Get Started | Sign Up | Contact Us>

VARIANT C — Retargeting (warm audience):
  Headline: <max 40 characters — assume they know you; drive urgency or FOMO>
  Body: <max 90 characters — reference what they already know + a new reason to act now>

Return ONLY the formatted ad copy.\
"""


def landing_page_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are a conversion copywriter.
Repurpose the source content into a single landing page section — think "above the fold hero" or "key benefits section".

{header}

OUTPUT FORMAT (use these exact labels):
HEADLINE: <max 10 words — outcome-led, specific, grounded in the core argument>
SUBHEADLINE: <max 20 words — expands the headline with one concrete fact or benefit>

BENEFIT BULLETS:
  ✓ <Benefit 1 — lead with the outcome, anchor with a fact if available>
  ✓ <Benefit 2>
  ✓ <Benefit 3>

SOCIAL PROOF LINE: <one sentence using a quote or stat from the source>

PRIMARY CTA: <button label, max 5 words>
SECONDARY CTA: <link text, max 6 words, softer commitment — e.g. "Read the full report">

Return ONLY the formatted landing page section.\
"""


def video_script_prompt(extraction: dict, brand_block: str = "", language: str = "english") -> str:
    header = _format_header(extraction, brand_block, language)
    return f"""\
You are a video content strategist writing a 60-second spoken script.
Repurpose the source content into a punchy, conversational video script.

{header}

OUTPUT FORMAT (use these exact labels and time codes):

[HOOK — 0 to 5 sec]
<1–2 sentences. Open with the most surprising fact or the one_sentence_summary. Spoken aloud — no jargon.>
[VISUAL: suggest a matching graphic, stat overlay, or B-roll clip]

[PROBLEM — 5 to 18 sec]
<2–3 sentences establishing the pain point the core_argument addresses.>
[VISUAL: suggest a relatable scene or pain-point graphic]

[SOLUTION — 18 to 42 sec]
<4–5 sentences. Cover 2–3 of the key_points conversationally. One sentence per point, no bullet-list cadence.>
[VISUAL: data visualisation or demonstration moment]

[PROOF — 42 to 52 sec]
<1–2 sentences. Quote a fact or verbatim quote from the source to build credibility.>
[VISUAL: stat card, quote overlay, or logo wall]

[CTA — 52 to 60 sec]
<1 sentence. Clear action. "Follow for more." / "Link in bio." / "Download the full report.">
[VISUAL: end card with CTA button graphic]

TOTAL WORD COUNT TARGET: 130–160 words (reads at ~150 words/min for a 60-second video).

Return ONLY the formatted script.\
"""


# ── Dispatch table ─────────────────────────────────────────────────────────────

FORMAT_PROMPTS = {
    "linkedin":     linkedin_prompt,
    "instagram":    instagram_prompt,
    "email":        email_prompt,
    "blog_summary": blog_summary_prompt,
    "ad_copy":      ad_copy_prompt,
    "landing_page": landing_page_prompt,
    "video_script": video_script_prompt,
}

FORMAT_META = {
    "linkedin":     {"label": "LinkedIn Post",         "content_type": "social",        "channel": "linkedin"},
    "instagram":    {"label": "Instagram Caption",     "content_type": "social",        "channel": "instagram"},
    "email":        {"label": "Email Newsletter",      "content_type": "email",         "channel": "email"},
    "blog_summary": {"label": "Blog Summary",          "content_type": "blog",          "channel": "blog"},
    "ad_copy":      {"label": "Ad Copy",               "content_type": "ad",            "channel": "ads"},
    "landing_page": {"label": "Landing Page Section",  "content_type": "landing_page",  "channel": "website"},
    "video_script": {"label": "Video Script",          "content_type": "other",         "channel": "other"},
}

VALID_FORMATS = set(FORMAT_PROMPTS)


def format_prompt(
    fmt: str,
    extraction: dict,
    brand_block: str = "",
    language: str = "english",
) -> str:
    """Dispatch to the correct format-specific prompt builder."""
    builder = FORMAT_PROMPTS.get(fmt)
    if builder is None:
        raise ValueError(f"Unknown format '{fmt}'. Valid formats: {sorted(VALID_FORMATS)}")
    return builder(extraction, brand_block, language)
