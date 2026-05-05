"""
app.py — SRH University AI Content Creator
Professional demo UI · Run: streamlit run app.py
"""

import io
import os
import re
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
    initial_sidebar_state="collapsed",
)

# ── Constants ─────────────────────────────────────────────────────────────────

SRH_ORANGE = "#E84E0F"

CONTENT_TYPES = {
    "blog":       ("📝", "Blog Post"),
    "social":     ("📱", "Social Media"),
    "program":    ("🎓", "Program Description"),
    "newsletter": ("📧", "Newsletter"),
}

TOPIC_SUGGESTIONS = {
    "blog":       ["AI Ethics at SRH", "Why Study in Berlin?", "The CORE Principle Explained", "Careers in Data Science"],
    "social":     ["Open Day June 2026", "New AI Programme Launch", "Student Success Story", "Berlin Campus Life"],
    "program":    ["MSc Applied Data Science and AI", "Executive MBA General Management", "BSc Computer Science", "MSc Big Data & Analytics"],
    "newsletter": ["April Campus Updates", "New Programme Launch", "Alumni Success Stories", "Open Day Invitation"],
}

AUDIENCES = [
    "Prospective Students",
    "Current Students",
    "Faculty & Staff",
    "Industry Partners",
    "Alumni",
]

TONES   = ["Academic", "Formal", "Professional", "Friendly", "Conversational"]
LENGTHS = {"Short": "~300 words", "Medium": "~650 words", "Long": "~1,000 words"}

KB_DIRS = {
    "primary":   [("PRIMARY SOURCES", "knowledge_base/primary/")],
    "secondary": [("SECONDARY SOURCES", "knowledge_base/secondary/")],
    "hybrid":    [
        ("PRIMARY SOURCES", "knowledge_base/primary/"),
        ("SECONDARY SOURCES", "knowledge_base/secondary/"),
    ],
}

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
  /* ── Chrome ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding: 0 !important; max-width: 100% !important; }}

  /* ── Two-panel layout ── */
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {{
      background: #FAFAFA;
      border-right: 1px solid #E8E8E8;
      padding: 2rem 1.8rem 3rem !important;
      min-height: 100vh;
  }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {{
      padding: 2rem 2.2rem 3rem !important;
      background: #FFFFFF;
  }}

  /* ── Section micro-labels ── */
  .mlabel {{
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #888;
      margin: 0.9rem 0 0.25rem;
  }}

  /* ── Content-type radio cards ── */
  div[data-testid="stRadio"] div[role="radiogroup"] label {{
      border: 1px solid #E0E0E0;
      border-radius: 8px;
      padding: 0.45rem 0.7rem;
      margin-bottom: 0.35rem;
      background: white;
      transition: border-color 0.15s, background 0.15s;
      width: 100%;
  }}
  div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {{
      border-color: {SRH_ORANGE};
      background: #FFF3EF;
  }}

  /* ── Generate button ── */
  div.stButton > button[kind="primary"] {{
      background: {SRH_ORANGE} !important;
      border: none !important;
      border-radius: 8px !important;
      font-weight: 700 !important;
      font-size: 1rem !important;
      padding: 0.7rem !important;
      color: white !important;
      width: 100%;
      margin-top: 0.5rem;
  }}
  div.stButton > button[kind="primary"]:hover {{
      filter: brightness(0.92) !important;
  }}

  /* ── Suggestion pills ── */
  div.stButton > button[kind="secondary"] {{
      border-radius: 5px !important;
      border: 1px solid #DDD !important;
      background: #F4F4F4 !important;
      color: #444 !important;
      font-size: 0.71rem !important;
      padding: 0 0.45rem !important;
      height: 32px !important;
      min-height: 32px !important;
      line-height: 1 !important;
  }}
  div.stButton > button[kind="secondary"]:hover {{
      border-color: {SRH_ORANGE} !important;
      background: #FFF0EC !important;
      color: {SRH_ORANGE} !important;
  }}

  /* ── Suggestion grid tightening ── */
  .mlabel-sug {{
      font-size: 0.63rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #AAA;
      margin: 0.25rem 0 0.15rem;
  }}
  /* Collapse extra vertical space Streamlit adds around each stButton */
  [data-testid="stColumn"] div.stButton {{
      margin-bottom: 0.15rem !important;
  }}
  @media (max-width: 640px) {{
      [data-testid="stHorizontalBlock"] {{ flex-direction: column !important; }}
  }}

  /* ── Tabs ── */
  div[data-testid="stTabs"] button[role="tab"] {{
      font-weight: 600;
      font-size: 0.88rem;
      padding: 0.5rem 1rem;
  }}
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
      border-bottom: 3px solid {SRH_ORANGE} !important;
      color: {SRH_ORANGE} !important;
  }}

  /* ── Status badge ── */
  .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: #F0FFF4;
      border: 1px solid #86EFAC;
      border-radius: 8px;
      padding: 0.45rem 0.9rem;
      font-size: 0.82rem;
      font-weight: 600;
      color: #166534;
      margin-bottom: 1.2rem;
  }}

  /* ── KB file cards ── */
  .kb-card {{
      background: #FAFAFA;
      border: 1px solid #EBEBEB;
      border-radius: 8px;
      padding: 0.55rem 0.85rem;
      margin-bottom: 0.35rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.84rem;
  }}
  .tag-primary   {{ background: #DBEAFE; color: #1D4ED8; font-size: 0.67rem; font-weight: 700;
                    padding: 0.1rem 0.45rem; border-radius: 999px; margin-right: 0.5rem; }}
  .tag-secondary {{ background: #FEF3C7; color: #B45309; font-size: 0.67rem; font-weight: 700;
                    padding: 0.1rem 0.45rem; border-radius: 999px; margin-right: 0.5rem; }}

  /* ── Diff highlights ── */
  mark.unique  {{ background: #BBF7D0; border-radius: 3px; padding: 0 2px; }}

  /* ── Divider spacing ── */
  hr {{ margin: 1rem 0 !important; }}

  /* ── Spinner color ── */
  [data-testid="stSpinner"] svg {{ stroke: {SRH_ORANGE}; }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_baseline() -> str:
    try:
        with open(os.path.join("examples", "chatgpt_output.md"), encoding="utf-8") as f:
            raw = f.read()
        lines = [l for l in raw.splitlines() if not l.strip().startswith("<!--")]
        return "\n".join(lines).strip()
    except FileNotFoundError:
        return ""


@st.cache_resource(show_spinner=False)
def load_kb(source: str) -> tuple[str, list[dict]]:
    from src.document_processor import MarkdownProcessor
    sections, meta = [], []
    for label, kb_dir in KB_DIRS[source]:
        try:
            docs = MarkdownProcessor(kb_dir).process_all()
            block = "\n\n---\n\n".join(f"### {d['filename']}\n{d['content']}" for d in docs)
            sections.append(f"## {label}\n\n{block}")
            for d in docs:
                meta.append({
                    "filename": d["filename"],
                    "words": len(d["content"].split()),
                    "source": "primary" if "primary" in kb_dir else "secondary",
                })
        except (FileNotFoundError, ValueError):
            pass
    return "\n\n===\n\n".join(sections), meta


def make_docx(content: str, topic: str) -> bytes:
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading(topic, 0)
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            doc.add_heading(stripped[4:], 3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], 2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], 1)
        elif stripped.startswith("- "):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        else:
            p = doc.add_paragraph(stripped)
            p.runs[0].font.size = Pt(11) if p.runs else None
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def highlight_unique(our: str, theirs: str) -> str:
    their_words = {w.lower() for w in re.findall(r'\b\w{5,}\b', theirs)}
    def tag(m):
        w = m.group(0)
        return f'<mark class="unique">{w}</mark>' if w.lower() not in their_words else w
    lines = []
    for line in our.splitlines():
        if line.startswith(("#", "`", "|")):
            lines.append(line)
        else:
            lines.append(re.sub(r'\b[A-Z][a-zA-Z]{4,}\b', tag, line))
    return "<br>".join(lines)


# ── Session state ─────────────────────────────────────────────────────────────

DEFAULTS = {
    "generated": None, "file_meta": [],
    "last_topic": "", "last_type": "blog",
    "last_language": "english", "last_kb_source": "hybrid",
    "last_audience": "Prospective Students",
    "last_tone": "Professional", "last_length": "Medium",
    "topic_val": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Layout ────────────────────────────────────────────────────────────────────

left, right = st.columns([1, 1.55], gap="small")

# ════════════════════════════════════════════════════════
# LEFT PANEL
# ════════════════════════════════════════════════════════
with left:
    st.image("assets/srh_logo.png", width=110)
    st.markdown("#### AI Content Creator")
    st.divider()

    # Content type
    st.markdown('<p class="mlabel">Content Type</p>', unsafe_allow_html=True)
    content_type = st.radio(
        "ctype",
        options=list(CONTENT_TYPES.keys()),
        format_func=lambda x: f"{CONTENT_TYPES[x][0]}  {CONTENT_TYPES[x][1]}",
        label_visibility="collapsed",
    )

    st.divider()

    # Topic + suggestions
    st.markdown('<p class="mlabel">Topic</p>', unsafe_allow_html=True)
    topic = st.text_input(
        "topic",
        value=st.session_state.topic_val,
        placeholder=f"e.g. {TOPIC_SUGGESTIONS[content_type][0]}",
        label_visibility="collapsed",
    )

    st.markdown('<p class="mlabel-sug">Suggestions</p>', unsafe_allow_html=True)
    sug_cols = st.columns(2, gap="small")
    for i, sug in enumerate(TOPIC_SUGGESTIONS[content_type][:4]):
        if sug_cols[i % 2].button(sug, key=f"sug_{sug}", use_container_width=True):
            st.session_state.topic_val = sug
            st.rerun()

    st.divider()

    # Audience
    st.markdown('<p class="mlabel">Audience</p>', unsafe_allow_html=True)
    audience = st.selectbox("audience", AUDIENCES, label_visibility="collapsed")

    st.divider()

    # Advanced options
    with st.expander("⚙️  Advanced Options", expanded=False):

        st.markdown('<p class="mlabel">Language</p>', unsafe_allow_html=True)
        language = st.radio(
            "lang", ["english", "german"],
            format_func=lambda x: "🇬🇧 English" if x == "english" else "🇩🇪 German",
            horizontal=True, label_visibility="collapsed",
        )

        st.markdown('<p class="mlabel">Knowledge Base</p>', unsafe_allow_html=True)
        kb_source = st.radio(
            "kb", ["hybrid", "primary", "secondary"],
            format_func=lambda x: {
                "hybrid":    "🟢 Hybrid — Primary + Secondary",
                "primary":   "🔵 Primary only",
                "secondary": "🟡 Secondary only",
            }[x],
            label_visibility="collapsed",
        )

        st.markdown('<p class="mlabel">Tone</p>', unsafe_allow_html=True)
        tone = st.select_slider(
            "tone", options=TONES, value="Professional",
            label_visibility="collapsed",
        )

        st.markdown('<p class="mlabel">Length</p>', unsafe_allow_html=True)
        length = st.radio(
            "length",
            list(LENGTHS.keys()),
            format_func=lambda x: f"{x}  ({LENGTHS[x]})",
            horizontal=True, label_visibility="collapsed",
        )

    st.divider()

    generate_btn = st.button(
        f"✨  Generate {CONTENT_TYPES[content_type][1]}",
        type="primary", use_container_width=True,
    )
    st.caption("Powered by GPT-4o-mini · SRH Knowledge Base")

# ════════════════════════════════════════════════════════
# RIGHT PANEL
# ════════════════════════════════════════════════════════
with right:

    # ── Generation ────────────────────────────────────────
    if generate_btn:
        active_topic = st.session_state.topic_val if not topic.strip() else topic
        if not active_topic.strip():
            st.warning("Please enter a topic before generating.")
        elif not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is not set. Add it to your `.env` file and restart.")
        else:
            try:
                with st.spinner("Loading SRH knowledge base…"):
                    kb_context, file_meta = load_kb(kb_source)

                style_preamble = (
                    f"GENERATION SETTINGS — follow these precisely:\n"
                    f"  Tone    : {tone}\n"
                    f"  Length  : {LENGTHS[length]}\n"
                    f"  Audience: {audience}\n\n"
                )

                with st.spinner(f"Generating {CONTENT_TYPES[content_type][1]}…"):
                    pipeline = Pipeline(language=language)
                    pipeline.kb_context = style_preamble + kb_context
                    pipeline.monitor(
                        topic=active_topic, content_type=content_type,
                        audience=audience, extra="",
                    )
                    content = pipeline.publish()

                st.session_state.generated    = content
                st.session_state.file_meta    = file_meta
                st.session_state.last_topic   = active_topic
                st.session_state.last_type    = content_type
                st.session_state.last_language = language
                st.session_state.last_kb_source = kb_source
                st.session_state.last_audience  = audience
                st.session_state.last_tone      = tone
                st.session_state.last_length    = length

            except ContentGeneratorError as e:
                st.error(f"Generation failed:\n{e}")
            except (FileNotFoundError, ValueError) as e:
                st.error(f"Knowledge base error:\n{e}")

    # ── Output ────────────────────────────────────────────
    if st.session_state.generated:
        s = st.session_state
        lang_flag = "🇩🇪" if s.last_language == "german" else "🇬🇧"
        kb_dot    = {"hybrid": "🟢", "primary": "🔵", "secondary": "🟡"}[s.last_kb_source]
        st.markdown(
            f'<div class="status-badge">✅ &nbsp;{CONTENT_TYPES[s.last_type][0]} {CONTENT_TYPES[s.last_type][1]}'
            f' &nbsp;·&nbsp; {lang_flag} {s.last_language.title()}'
            f' &nbsp;·&nbsp; {kb_dot} {s.last_kb_source.title()} KB'
            f' &nbsp;·&nbsp; {s.last_tone} &nbsp;·&nbsp; {s.last_length}'
            f'</div>',
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3 = st.tabs([
            "📄  Generated Content",
            "🔍  Uniqueness Analysis",
            "📚  Knowledge Base Used",
        ])

        # ── Tab 1 ─────────────────────────────────────────
        with tab1:
            st.markdown(s.generated)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "⬇️  Download .md", data=s.generated,
                    file_name=f"srh_{s.last_type}_{s.last_language}.md",
                    mime="text/markdown", use_container_width=True,
                )
            with c2:
                try:
                    docx_bytes = make_docx(s.generated, s.last_topic)
                    st.download_button(
                        "⬇️  Download .docx", data=docx_bytes,
                        file_name=f"srh_{s.last_type}_{s.last_language}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except ImportError:
                    st.caption("Install `python-docx` for Word export.")

        # ── Tab 2 ─────────────────────────────────────────
        with tab2:
            baseline = load_baseline()
            if not baseline:
                st.info("No ChatGPT baseline found. Add content to `examples/chatgpt_output.md`.")
            else:
                col_ours, col_theirs = st.columns(2)
                with col_ours:
                    st.markdown("**🟢 Our RAG System**")
                    st.caption("Green highlight = terms unique to our output, not in ChatGPT's")
                    highlighted = highlight_unique(s.generated, baseline)
                    st.markdown(highlighted, unsafe_allow_html=True)
                with col_theirs:
                    st.markdown("**⚪ ChatGPT Baseline**")
                    st.caption("Public knowledge only — no SRH context provided")
                    st.markdown(baseline)

                st.divider()
                st.markdown("**Factual specificity scorecard**")
                st.markdown("""
| Criterion | ChatGPT | Our System |
|---|:---:|:---:|
| CORE principle — specific details | ⚠️ Generic | ✅ |
| 5-week block / 8 ECTS structure | ❌ | ✅ |
| Named alumni quote + job title | ❌ | ✅ |
| 140+ countries statistic | ❌ | ✅ |
| Career:Skills programme named | ❌ | ✅ |
| SRH brand voice enforced | ❌ | ✅ |
| British English throughout | ❌ | ✅ |
                """)

        # ── Tab 3 ─────────────────────────────────────────
        with tab3:
            meta = s.file_meta
            if not meta:
                st.info("No file metadata available — regenerate content to populate this tab.")
            else:
                primary_files   = [f for f in meta if f["source"] == "primary"]
                secondary_files = [f for f in meta if f["source"] == "secondary"]

                if primary_files:
                    st.markdown(f"**🔵 Primary Sources** &nbsp;—&nbsp; {len(primary_files)} files")
                    for f in primary_files:
                        st.markdown(
                            f'<div class="kb-card">'
                            f'<span><span class="tag-primary">PRIMARY</span>{f["filename"]}</span>'
                            f'<span style="color:#999;font-size:0.78rem">{f["words"]:,} words</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                if secondary_files:
                    st.markdown(f"**🟡 Secondary Sources** &nbsp;—&nbsp; {len(secondary_files)} files")
                    for f in secondary_files:
                        st.markdown(
                            f'<div class="kb-card">'
                            f'<span><span class="tag-secondary">SECONDARY</span>{f["filename"]}</span>'
                            f'<span style="color:#999;font-size:0.78rem">{f["words"]:,} words</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                total_words = sum(f["words"] for f in meta)
                st.divider()
                st.markdown(
                    f"**Total context injected:** {total_words:,} words across {len(meta)} documents"
                )

    # ── Welcome state ──────────────────────────────────────
    else:
        st.markdown("## Welcome to the SRH AI Content Creator")
        st.markdown(
            "Select a content type, enter your topic, and click **Generate** — "
            "the system will ground every word in SRH's own knowledge base."
        )
        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
<div style="border:1px solid #E8E8E8;border-radius:12px;padding:1.2rem;">
<b>Why this is different from ChatGPT</b><br><br>
✅ &nbsp;Named alumni quotes (Hassan Hadeed, QESTRIT GmbH)<br>
✅ &nbsp;Exact program details — 5-week blocks, 8 ECTS cap<br>
✅ &nbsp;"140 countries" stat — not "diverse student body"<br>
✅ &nbsp;Career:Skills programme named correctly<br>
✅ &nbsp;CORE principle explained — not just mentioned<br>
✅ &nbsp;SRH brand voice rules enforced by prompt<br>
✅ &nbsp;Bilingual output — English & German<br>
</div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""
<div style="border:1px solid #E8E8E8;border-radius:12px;padding:1.2rem;">
<b>Content types</b><br><br>
📝 &nbsp;<b>Blog Post</b> — 700–1,000 words, thought leadership<br><br>
📱 &nbsp;<b>Social Media</b> — LinkedIn + Instagram, dual format<br><br>
🎓 &nbsp;<b>Program Description</b> — prospectus-ready copy<br><br>
📧 &nbsp;<b>Newsletter</b> — full email with subject, sections & CTA<br>
</div>""", unsafe_allow_html=True)

        st.divider()
        with st.expander("📚  Knowledge Base Overview"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""
**🔵 Primary Sources**
- `srh_brand_guidelines.md` — voice & tone rules
- `srh_program_specs.md` — programs, fees, structure
- `srh_career_outcomes.md` — employment stats & partners
- `srh_student_success_stories.md` — alumni quotes
- `srh_newsletter_examples.md` — past campaigns
                """)
            with c2:
                st.markdown("""
**🟡 Secondary Sources**
- `competitor_analysis.md` — Berlin market & benchmarks
- `career_trends.md` — industry demand signals
- `email_benchmarks_education_marketing.md` — channel data
- `eu_ai_act_guidelines.md` — regulatory context
                """)
