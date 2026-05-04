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

**5. Build the index and generate content**
```bash
# Build the vector index from all knowledge base documents
python -m src.main --refresh-kb

# Generate a blog post
python -m src.main --type blog_post --topic "AI programs at SRH" --audience "prospective students"

# Generate a social media post and save to file
python -m src.main --type social_media --topic "Open day 2026" --audience "high school graduates" --output output/open_day_post.md
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
