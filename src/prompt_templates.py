"""
prompt_templates.py

Centralised library of prompt templates for each content type.
Responsibilities:
  - Provide structured system and user prompts for blog posts, social media, emails, etc.
  - Inject retrieved context (RAG chunks) and user-supplied variables into templates
  - Enforce SRH University tone, brand voice, and compliance guardrails
"""

SRH_VOICE_RULES = """
SRH Brand Voice Rules (apply to every piece of content):
- Tone: Confident, warm, and expert — never corporate-speak or generic.
- Perspective: Student-first; speak to aspirations, not just program features.
- Differentiators to weave in: CORE principle (Competence-Oriented Research and Education),
  Berlin ecosystem, small cohorts, dual-study options, applied learning, international diversity.
- Avoid: Hollow superlatives ("world-class", "cutting-edge"), passive voice, and filler phrases.
- Claims: Only reference specific programs, outcomes, or statistics that appear in the context below.
- Language: British English unless the audience is explicitly North American.
"""


def blog_post_template(kb_context: str, topic: str) -> str:
    """
    Generate a long-form blog post grounded in SRH knowledge base content.

    Use this template when producing thought-leadership articles, program spotlights,
    student advice pieces, or trend analysis for the SRH website or Medium channel.
    Aim for 700–1,000 words. The model should cite specific programs or outcomes
    drawn from kb_context rather than inventing details.

    Args:
        kb_context: Relevant chunks retrieved from the SRH knowledge base.
        topic: The specific angle or question the post should address.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    return f"""You are a senior content strategist writing for SRH University's blog.
Your task is to produce an engaging, expert-led blog post on the topic below.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

TOPIC: {topic}

OUTPUT REQUIREMENTS:
- Length: 700–1,000 words.
- Structure: Hook opening (no generic "In today's world…" openers), 2–4 body sections with
  subheadings, and a closing call-to-action linking to an SRH program or open day.
- Back every claim with evidence from the context above — no invented statistics.
- End with a one-sentence meta description (prefixed "Meta:") suitable for SEO.
- Format in Markdown.
"""


def social_media_template(kb_context: str, announcement: str) -> str:
    """
    Create a dual-format LinkedIn and Instagram post for an SRH announcement.

    Use this template for program launches, open days, alumni spotlights, rankings news,
    or partnership announcements. Returns two posts in one response: one optimised for
    LinkedIn (professional, ~150 words) and one for Instagram (punchy, emoji-light, ~60 words).
    The model should anchor each post to a concrete SRH differentiator from kb_context.

    Args:
        kb_context: Relevant chunks retrieved from the SRH knowledge base.
        announcement: The specific news or event to promote.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    return f"""You are SRH University's social media manager.
Write two posts for the announcement below — one for LinkedIn, one for Instagram.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

ANNOUNCEMENT: {announcement}

OUTPUT FORMAT (use these exact headings):

## LinkedIn Post
- Length: 100–150 words.
- Open with a bold insight or stat from the context, not a generic greeting.
- Highlight one specific SRH differentiator (CORE principle, Berlin location, cohort size, etc.).
- Close with a clear CTA (link in bio / register now / learn more).
- Include 3–5 relevant hashtags at the end.

## Instagram Post
- Length: 50–70 words.
- Punchy and visual in tone — write as if paired with a strong image.
- Use 1–2 emojis maximum; no emoji spam.
- Include 5–8 hashtags on a separate line.
"""


def program_description_template(kb_context: str, program_name: str) -> str:
    """
    Write a polished program description for the SRH website or prospectus.

    Use this template for degree program pages, brochure copy, or admissions portal listings.
    Output includes a headline, overview paragraph, key features list, career outcomes,
    and an entry requirements summary — all grounded in kb_context so details are accurate.
    The dual-study structure should be surfaced where the program supports it.

    Args:
        kb_context: Relevant chunks retrieved from the SRH knowledge base (program specs,
                    career outcomes, brand guidelines).
        program_name: Full official name of the program (e.g. "Executive MBA General Management").

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    return f"""You are a higher-education copywriter producing official program copy for SRH University.
Write a complete program description for the program specified below.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

PROGRAM: {program_name}

OUTPUT STRUCTURE (use these exact headings, format in Markdown):

## [Program Name] — Headline
A single punchy headline (max 12 words) that leads with the student outcome, not the institution.

## Overview
2–3 sentences: what the program is, who it is for, and what makes the SRH approach distinctive
(CORE principle, applied learning, Berlin ecosystem). No invented facts.

## What You Will Learn
Bullet list of 4–6 concrete competencies or modules drawn from the context.

## Study Format
Describe full-time / part-time / dual-study options available. Flag dual-study explicitly if supported.

## Career Outcomes
2–3 sentences backed by specific roles, sectors, or statistics present in the context.

## Entry Requirements
Concise bullet list: academic background, language proficiency, work experience (if applicable).

## Next Step
One-sentence CTA directing the reader to apply or attend an info session.
"""


def render_template(template: str, variables: dict) -> str:
    """Inject variables into a template string using str.format_map."""
    pass


def build_system_prompt(content_type: str) -> str:
    """Return the appropriate system-level prompt for the requested content type."""
    pass


def build_user_prompt(content_type: str, context_chunks: list[str], variables: dict) -> str:
    """Combine retrieved context chunks with user variables into a final user prompt."""
    pass
