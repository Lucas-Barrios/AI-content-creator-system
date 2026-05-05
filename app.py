"""
app.py — SRH University AI Content Creator
Streamlit web interface for demo purposes.

Run with: streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

from src.content_pipeline import Pipeline
from src.llm_integration import ContentGeneratorError

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SRH AI Content Creator",
    page_icon="🎓",
    layout="wide",
)

# ── Load ChatGPT baseline for comparison ──────────────────────────────────────

def load_baseline() -> str:
    path = os.path.join("examples", "chatgpt_output.md")
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        # Strip HTML comment lines used as placeholders
        lines = [l for l in raw.splitlines() if not l.strip().startswith("<!--")]
        return "\n".join(lines).strip()
    except FileNotFoundError:
        return "_No ChatGPT baseline found. Add content to `examples/chatgpt_output.md`._"


# ── Cache KB loading so it doesn't re-read files on every interaction ─────────

KB_DIRS = {
    "primary":   [("PRIMARY SOURCES (Brand, Programs, Alumni)", "knowledge_base/primary/")],
    "secondary": [("SECONDARY SOURCES (Market Research, Competitor Analysis)", "knowledge_base/secondary/")],
    "hybrid":    [
        ("PRIMARY SOURCES (Brand, Programs, Alumni)", "knowledge_base/primary/"),
        ("SECONDARY SOURCES (Market Research, Competitor Analysis)", "knowledge_base/secondary/"),
    ],
}


@st.cache_resource(show_spinner=False)
def load_knowledge_base(source: str) -> tuple[str, list[str]]:
    from src.document_processor import MarkdownProcessor

    sections = []
    filenames = []

    for label, kb_dir in KB_DIRS[source]:
        try:
            processor = MarkdownProcessor(kb_dir)
            docs = processor.process_all()
            block = "\n\n---\n\n".join(f"### {doc['filename']}\n{doc['content']}" for doc in docs)
            sections.append(f"## {label}\n\n{block}")
            filenames.extend(d["filename"] for d in docs)
        except (FileNotFoundError, ValueError):
            pass

    return "\n\n===\n\n".join(sections), filenames


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("assets/srh_logo.png", width=160)
    st.title("Content Settings")
    st.divider()

    content_type = st.selectbox(
        "Content Type",
        options=["blog", "social", "program"],
        format_func=lambda x: {
            "blog": "📝 Blog Post",
            "social": "📱 Social Media",
            "program": "🎓 Program Description",
        }[x],
    )

    topic = st.text_input(
        "Topic",
        placeholder={
            "blog": "e.g. AI Ethics at SRH",
            "social": "e.g. Open Day June 2026",
            "program": "e.g. MSc Applied Data Science and AI",
        }[content_type],
    )

    if content_type == "social":
        extra = st.text_input("Announcement text", placeholder="e.g. Join us on 14 June in Berlin")
    elif content_type == "program":
        extra = st.text_input("Program name (if different from topic)", placeholder="e.g. MSc Applied Data Science and AI")
    else:
        extra = ""

    language = st.radio(
        "Output Language",
        options=["english", "german"],
        format_func=lambda x: "🇬🇧 English" if x == "english" else "🇩🇪 German",
        horizontal=True,
    )

    kb_source = st.radio(
        "Knowledge Base",
        options=["hybrid", "primary", "secondary"],
        format_func=lambda x: {
            "primary":   "🔵 Primary only",
            "secondary": "🟡 Secondary only",
            "hybrid":    "🟢 Hybrid (Primary + Secondary)",
        }[x],
        help=(
            "**Primary** — SRH brand guidelines, program specs, alumni stories.\n\n"
            "**Secondary** — Market research, competitor analysis, career trends.\n\n"
            "**Hybrid** — Both combined for the richest context."
        ),
    )

    st.divider()
    generate_btn = st.button("✨ Generate Content", use_container_width=True, type="primary")

    st.divider()
    st.caption("Powered by GPT-4o-mini · SRH Knowledge Base")


# ── Main area ─────────────────────────────────────────────────────────────────

st.title("🎓 SRH University AI Content Creator")
st.caption("RAG-powered content grounded in SRH's own knowledge base — brand-accurate, specific, and on-voice.")

# Session state init
if "generated" not in st.session_state:
    st.session_state.generated = None
if "last_topic" not in st.session_state:
    st.session_state.last_topic = ""
if "last_language" not in st.session_state:
    st.session_state.last_language = "english"
if "last_kb_source" not in st.session_state:
    st.session_state.last_kb_source = "hybrid"

# ── Generation ────────────────────────────────────────────────────────────────

if generate_btn:
    if not topic.strip():
        st.warning("Please enter a topic before generating.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set. Add it to your `.env` file and restart.")
    else:
        try:
            with st.spinner("Loading knowledge base…"):
                kb_context, filenames = load_knowledge_base(kb_source)

            with st.spinner(f"Generating {content_type} in {language}…"):
                pipeline = Pipeline(language=language)
                pipeline.kb_context = kb_context
                pipeline.monitor(
                    topic=topic,
                    content_type=content_type,
                    audience="prospective international students",
                    extra=extra,
                )
                content = pipeline.publish()

            st.session_state.generated = content
            st.session_state.last_topic = topic
            st.session_state.last_language = language
            st.session_state.last_kb_source = kb_source

        except ContentGeneratorError as e:
            st.error(f"Generation failed: {e}")
        except (FileNotFoundError, ValueError) as e:
            st.error(f"Knowledge base error: {e}")

# ── Output display ────────────────────────────────────────────────────────────

if st.session_state.generated:
    content = st.session_state.generated
    lang_label = "🇩🇪 German" if st.session_state.last_language == "german" else "🇬🇧 English"
    kb_label = {"primary": "🔵 Primary", "secondary": "🟡 Secondary", "hybrid": "🟢 Hybrid"}[st.session_state.last_kb_source]
    st.success(f"Generated · {lang_label} · {kb_label} KB · topic: _{st.session_state.last_topic}_")

    show_comparison = st.toggle("📊 Show side-by-side comparison with ChatGPT baseline")

    if show_comparison:
        col_ours, col_chatgpt = st.columns(2)

        with col_ours:
            st.subheader("Our RAG System")
            st.caption("Grounded in SRH knowledge base · brand voice enforced")
            st.markdown(content)
            st.download_button(
                label="⬇ Download our output",
                data=content,
                file_name=f"srh_{content_type}_{st.session_state.last_language}.md",
                mime="text/markdown",
            )

        with col_chatgpt:
            st.subheader("ChatGPT Baseline")
            st.caption("No knowledge base · public information only")
            baseline = load_baseline()
            st.markdown(baseline)

        st.divider()
        st.subheader("Why ours is different")
        st.markdown("""
| | ChatGPT | Our System |
|---|:---:|:---:|
| Mentions CORE principle with specifics | ⚠️ Generic | ✅ Exact details |
| Cites 5-week block / 8 ECTS structure | ❌ | ✅ |
| Named alumni quote | ❌ | ✅ |
| 140+ countries stat | ❌ | ✅ |
| Career:Skills programme | ❌ | ✅ |
| SRH brand voice rules | ❌ | ✅ |
| British English | ❌ | ✅ |
        """)

    else:
        st.markdown(content)
        st.download_button(
            label="⬇ Download as Markdown",
            data=content,
            file_name=f"srh_{content_type}_{st.session_state.last_language}.md",
            mime="text/markdown",
        )

else:
    # Welcome state
    st.info("Configure your content in the sidebar and click **✨ Generate Content** to begin.")

    with st.expander("How it works", expanded=True):
        st.markdown("""
**Five-stage pipeline:**

1. **Document** — Loads and parses all SRH knowledge base files
2. **Monitor** — Identifies the content need (type, topic, audience, language)
3. **Brief** — Scans the knowledge base for relevant facts and proof points
4. **Publish** — Injects context into a brand-voice prompt and calls GPT-4o-mini
5. **Iterate** — Captures feedback for the next generation cycle

**Knowledge base — primary sources**
- `srh_brand_guidelines.md` — voice, tone, and style rules
- `srh_program_specs.md` — degree programs, fees, locations
- `srh_career_outcomes.md` — employment stats and partner companies
- `srh_student_success_stories.md` — named alumni quotes
- `srh_newsletter_examples.md` — annotated past campaigns

**Knowledge base — secondary sources**
- `competitor_analysis.md` — Berlin market and international benchmarks
- `german_higher_ed_trends.md` / `berlin_education_market.rtf` — market research
- `career_trends.md` — industry demand signals
- `email_benchmarks_education_marketing.md` — channel benchmarks
- `student_needs.rtf` — prospective student pain points
        """)
