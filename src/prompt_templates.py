"""
prompt_templates.py

Centralised library of prompt templates for each content type.
Responsibilities:
  - Provide structured system and user prompts for blog posts, social media, emails, etc.
  - Inject retrieved context (RAG chunks) and user-supplied variables into templates
  - Enforce SRH University tone, brand voice, and compliance guardrails
"""

BLOG_POST_TEMPLATE = """
You are a content writer for SRH University. Using the context below, write a blog post.

Context:
{context}

Topic: {topic}
Audience: {audience}
Tone: Professional yet approachable
Word count: ~{word_count}
"""

SOCIAL_MEDIA_TEMPLATE = """
You are a social media manager for SRH University. Write a {platform} post.

Context:
{context}

Topic: {topic}
Character limit: {char_limit}
Include hashtags: {include_hashtags}
"""

EMAIL_TEMPLATE = """
You are writing on behalf of SRH University admissions. Draft a {email_type} email.

Context:
{context}

Subject line: {subject}
Recipient: {recipient_type}
Call to action: {cta}
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
