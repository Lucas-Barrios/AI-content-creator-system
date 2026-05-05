# SRH University — AI Content Creator

A RAG-powered content generation system that produces on-brand marketing and admissions content using SRH University's own knowledge base.

## Architecture

```
knowledge_base/ → document_processor → knowledge_base (vector index)
                                              ↓
                          user request → content_pipeline
                                              ↓
                          prompt_templates + llm_integration → output
```

| Module | Responsibility |
|---|---|
| `document_processor.py` | Load, clean, and chunk raw documents |
| `knowledge_base.py` | Embed chunks and retrieve relevant context |
| `prompt_templates.py` | Brand-safe prompt templates per content type |
| `llm_integration.py` | API calls to Anthropic / OpenAI |
| `content_pipeline.py` | Orchestrate the full retrieve → generate flow |
| `main.py` | CLI entry point |

## Setup

**1. Clone and create a virtual environment**
```bash
git clone <repo-url>
cd ai-content-creator
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
cp .env.example .env
# Open .env and add your API keys
```

**4. Populate the knowledge base**

Add your content to the Markdown files in `knowledge_base/`:
- `knowledge_base/primary/brand_guidelines.md` — voice, tone, style rules
- `knowledge_base/primary/program_specs.md` — degree programs, fees, locations
- `knowledge_base/primary/past_content/` — drop in previous campaigns
- `knowledge_base/secondary/german_higher_ed_trends.md` — market research
- `knowledge_base/secondary/competitor_analysis.md` — competitor insights

**5. Run the web interface (recommended for demos)**
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`. The sidebar lets you pick content type, topic, and language. Toggle the comparison view to see our system vs. the ChatGPT baseline side by side.

**Or use the CLI**
```bash
# Blog post in English
python main.py --type blog --topic "AI Ethics at SRH"

# Blog post in German
python main.py --type blog --topic "KI-Ethik an der SRH" --language german

# Social media posts
python main.py --type social --topic "Open Day June 2026" --extra "Join us 14 June in Berlin"

# Program description
python main.py --type program --topic "MSc Applied Data Science and AI"

# Full pipeline demo (all 5 stages)
python main.py --type demo
```

## Content Types

- `blog_post` — long-form article (~800–1200 words)
- `social_media` — short post for LinkedIn / Instagram
- `email` — admissions or newsletter email
- `landing_page` — program landing page copy
- `press_release` — formal announcement

## Project Structure

```
ai-content-creator/
├── src/                   # Application source code
├── knowledge_base/
│   ├── primary/           # Official SRH documents (high authority)
│   └── secondary/         # Market research (supporting context)
├── templates/             # Output format templates (Markdown, HTML)
├── config/
│   └── vscode_agent.json  # Agent configuration
├── .env.example           # Environment variable template
├── requirements.txt
└── README.md
```
