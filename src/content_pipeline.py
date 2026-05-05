"""
content_pipeline.py

Orchestrates the end-to-end content generation workflow.
Stages: document → monitor → brief → publish → iterate
"""

from src.document_processor import MarkdownProcessor
from src.prompt_templates import blog_post_template, social_media_template, program_description_template, newsletter_template
from src.llm_integration import ContentGenerator


class Pipeline:
    """Five-stage content pipeline: ingest → identify need → brief → generate → refine."""

    def __init__(self, kb_dir: str = "knowledge_base/primary/", language: str = "english"):
        self.kb_dir = kb_dir
        self.language = language
        self.kb_context: str = ""
        self.content_need: dict = {}
        self.content_brief: str = ""
        self.output: str = ""

    # ── Stage 1 ───────────────────────────────────────────────────────────────

    def document(self) -> str:
        """
        Ingest all Markdown files from the knowledge base directory.
        Returns a combined context string ready for prompt injection.
        """
        processor = MarkdownProcessor(self.kb_dir)
        docs = processor.process_all()
        self.kb_context = "\n\n---\n\n".join(
            f"### {doc['filename']}\n{doc['content']}" for doc in docs
        )
        return f"Loaded {len(docs)} documents: {', '.join(d['filename'] for d in docs)}"

    # ── Stage 2 ───────────────────────────────────────────────────────────────

    def monitor(self, topic: str, content_type: str = "blog_post", audience: str = "prospective students", extra: str = "") -> str:
        """
        Identify a content need and store it for the next stage.
        In production this would scan a content calendar or CMS gap analysis.
        Here it accepts an explicit brief from the caller.

        Args:
            extra: Secondary variable used by some templates —
                   announcement text for social_media, program name for program_description.
        """
        self.content_need = {
            "topic": topic,
            "content_type": content_type,
            "audience": audience,
            "extra": extra,
        }
        return (
            f"Content need identified:\n"
            f"  Type     : {content_type}\n"
            f"  Topic    : {topic}\n"
            f"  Audience : {audience}\n"
            f"  Language : {self.language}"
        )

    # ── Stage 3 ───────────────────────────────────────────────────────────────

    def brief(self) -> str:
        """
        Build a content brief by scanning the knowledge base for the most
        relevant facts, stats, and proof points for the identified topic.
        Returns a plain-text brief summary (not yet a full LLM prompt).
        """
        topic = self.content_need.get("topic", "")

        # Pull sentences from the context that mention key topic words
        keywords = [w.lower() for w in topic.split() if len(w) > 4]
        relevant_lines = []
        for line in self.kb_context.splitlines():
            if any(kw in line.lower() for kw in keywords):
                stripped = line.strip("# ").strip()
                if stripped and len(stripped) > 40:
                    relevant_lines.append(f"  • {stripped}")

        hits = relevant_lines[:6] if relevant_lines else ["  • No direct matches — will use full context."]
        self.content_brief = "\n".join(hits)
        return f"Brief — key knowledge base insights for '{topic}':\n{self.content_brief}"

    # ── Stage 4 ───────────────────────────────────────────────────────────────

    def publish(self) -> str:
        """
        Build the LLM prompt from the correct template and call ContentGenerator.
        Selects template based on content_type set in monitor().
        Returns the generated content string.
        """
        content_type = self.content_need.get("content_type", "blog_post")
        topic = self.content_need.get("topic", "")
        extra = self.content_need.get("extra", topic)

        if content_type == "social":
            prompt = social_media_template(self.kb_context, announcement=extra or topic, language=self.language)
        elif content_type == "program":
            prompt = program_description_template(self.kb_context, program_name=extra or topic, language=self.language)
        elif content_type == "newsletter":
            prompt = newsletter_template(self.kb_context, topic, language=self.language)
        else:  # default: blog_post
            prompt = blog_post_template(self.kb_context, topic, language=self.language)

        generator = ContentGenerator()
        self.output = generator.generate_content(prompt)
        return self.output

    # ── Stage 5 ───────────────────────────────────────────────────────────────

    def iterate(self, feedback: str = "") -> str:
        """
        Refine the published output based on feedback.
        In production this would re-prompt with the original output + critique.
        Here it appends the feedback as an editorial note for the next run.
        """
        if not feedback:
            return "No feedback provided — output accepted as-is."

        note = (
            f"Editorial note for next iteration:\n"
            f"  {feedback}\n\n"
            f"Action: re-run publish() after updating the prompt template or knowledge base."
        )
        return note
