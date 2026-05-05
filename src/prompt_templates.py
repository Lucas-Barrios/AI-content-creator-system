"""
prompt_templates.py

Centralised library of prompt templates for each content type.
Responsibilities:
  - Provide structured system and user prompts for blog posts, social media, emails, etc.
  - Inject retrieved context (RAG chunks) and user-supplied variables into templates
  - Enforce SRH University tone, brand voice, and compliance guardrails
"""

SUPPORTED_LANGUAGES = {"english", "german"}

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

GERMAN_VOICE_ADDENDUM = """
German Language Rules (apply in addition to all brand voice rules above):
- Write entirely in German — headings, body, CTA, and meta description.
- Use formal "Sie" address throughout (not "du").
- Maintain British English spellings for any English proper nouns (e.g. programme names).
- Adapt idioms naturally — do not translate English phrases word-for-word.
- For German audiences, lead with practical outcomes and career relevance; de-emphasise prestige language.
"""


def _validate_language(language: str) -> str:
    """Normalise and validate the language parameter. Returns the lowercased value."""
    normalised = language.strip().lower()
    if normalised not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. "
            f"Choose one of: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )
    return normalised


def _language_block(language: str) -> str:
    """Return the language instruction block to append to any template."""
    if language == "german":
        return f"\nOUTPUT LANGUAGE: German{GERMAN_VOICE_ADDENDUM}"
    return "\nOUTPUT LANGUAGE: English (British spelling throughout)"


def blog_post_template(kb_context: str, topic: str, language: str = "english") -> str:
    """
    Generate a long-form blog post grounded in SRH knowledge base content.

    Use this template when producing thought-leadership articles, program spotlights,
    student advice pieces, or trend analysis for the SRH website or Medium channel.
    Aim for 700–1,000 words. The model should cite specific programs or outcomes
    drawn from kb_context rather than inventing details.

    Args:
        kb_context: Relevant chunks retrieved from the SRH knowledge base.
        topic: The specific angle or question the post should address.
        language: Output language — 'english' or 'german'. Defaults to 'english'.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    language = _validate_language(language)
    return f"""You are a senior content strategist writing for SRH University's blog.
Your task is to produce an engaging, expert-led blog post on the topic below.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

TOPIC: {topic}

OUTPUT REQUIREMENTS:
- Length: 700–1,000 words.
- Structure: SRH-specific hook, 2–4 body sections with subheadings, closing CTA to an SRH program or open day.
- Back every claim with evidence from the context above — no invented statistics.
- End with a one-sentence meta description (prefixed "Meta:") suitable for SEO.
- Format in Markdown.

HOOK RULE — this is the most important instruction:
- The very first sentence must be a concrete, SRH-specific hook drawn from the context above.
- Use one of these hook types:
    a) A named student or alumni quote: e.g. "Hassan Hadeed was working as a software tester when he enrolled — 18 months later he was leading the team."
    b) A specific SRH stat or fact: e.g. "Students from 140 countries study together at SRH Berlin — and most of them graduate with a job offer already in hand."
    c) A surprising program detail: e.g. "At SRH, you never study more than one subject at a time — that single rule changes everything about how deeply you learn."
- NEVER open with: "In today's world…", "Artificial intelligence is transforming…", "Choosing the right university…", "In an era of…", or any scene-setting sentence about industry trends.
- If you cannot find a suitable hook in the context, open with the most specific SRH fact available rather than a generic statement.
{_language_block(language)}"""


def social_media_template(kb_context: str, announcement: str, language: str = "english") -> str:
    """
    Create a dual-format LinkedIn and Instagram post for an SRH announcement.

    Use this template for program launches, open days, alumni spotlights, rankings news,
    or partnership announcements. Returns two posts in one response: one optimised for
    LinkedIn (professional, ~150 words) and one for Instagram (punchy, emoji-light, ~60 words).
    The model should anchor each post to a concrete SRH differentiator from kb_context.

    Args:
        kb_context: Relevant chunks retrieved from the SRH knowledge base.
        announcement: The specific news or event to promote.
        language: Output language — 'english' or 'german'. Defaults to 'english'.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    language = _validate_language(language)
    return f"""You are SRH University's social media manager.
Write two posts for the announcement below — one for LinkedIn, one for Instagram.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

ANNOUNCEMENT: {announcement}

OUTPUT FORMAT (use these exact headings):

HOOK RULE — applies to both posts:
- The opening line must be a concrete, SRH-specific hook drawn from the context above.
- Preferred hook types:
    a) A named alumni result: e.g. "Hassan Hadeed enrolled as a tester. He graduated as a team lead."
    b) A specific SRH stat: e.g. "140 countries. One campus. One shared goal."
    c) A program detail that surprises: e.g. "One subject at a time. No distractions. That's CORE."
- NEVER open with: "Exciting news!", "We are thrilled to announce…", "In today's competitive landscape…", or any generic marketing phrase.

## LinkedIn Post
- Length: 100–150 words.
- First line: SRH-specific hook (see above).
- Highlight one specific SRH differentiator (CORE principle, Berlin location, cohort size, etc.).
- Close with a clear CTA (link in bio / register now / learn more).
- Include 3–5 relevant hashtags at the end.

## Instagram Post
- Length: 50–70 words.
- First line: punchy SRH-specific hook — write as if paired with a strong image.
- Use 1–2 emojis maximum; no emoji spam.
- Include 5–8 hashtags on a separate line.
{_language_block(language)}"""


def program_description_template(kb_context: str, program_name: str, language: str = "english") -> str:
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
        language: Output language — 'english' or 'german'. Defaults to 'english'.

    Returns:
        A formatted prompt string ready to send to the LLM.
    """
    language = _validate_language(language)
    return f"""You are a higher-education copywriter producing official program copy for SRH University.
Write a complete program description for the program specified below.

{SRH_VOICE_RULES}

--- KNOWLEDGE BASE CONTEXT ---
{kb_context}
--- END CONTEXT ---

PROGRAM: {program_name}

OUTPUT STRUCTURE (use these exact headings, format in Markdown):

HOOK RULE — applies to the Headline and Overview:
- The headline and the first sentence of the Overview must be grounded in a specific SRH fact, outcome, or program detail from the context above.
- Headline examples of the right style:
    a) Outcome-led: "Graduate job-ready — with real projects, real partners, real Berlin."
    b) Stat-led: "One subject at a time. Eight weeks. Deeper than any lecture ever could go."
    c) Quote-led: "'SRH gave me the ethics lens I use every day.' — MSc Data Science alumna."
- NEVER open the headline or overview with: "Welcome to…", "Are you ready to…", "In today's data-driven world…", or any phrase that could apply to any university.

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
{_language_block(language)}"""


def render_template(template: str, variables: dict) -> str:
    """Inject variables into a template string using str.format_map."""
    pass


def build_system_prompt(content_type: str) -> str:
    """Return the appropriate system-level prompt for the requested content type."""
    pass


def build_user_prompt(content_type: str, context_chunks: list[str], variables: dict) -> str:
    """Combine retrieved context chunks with user variables into a final user prompt."""
    pass
