# SRH University AI Content Creator

A knowledge-base grounded content generation system for on-brand SRH marketing and admissions content.

## Architecture

```txt
Next.js frontend
      ↓
Next.js API proxy routes
      ↓
FastAPI backend
      ↓
content_pipeline + prompt_templates + llm_integration
      ↓
OpenAI API
```

| Module | Responsibility |
|---|---|
| `api_server.py` / `app.py` | UI-agnostic FastAPI backend |
| `src/generation_service.py` | Request parsing, knowledge-base loading, generation orchestration |
| `src/content_pipeline.py` | Document → monitor → brief → publish → iterate flow |
| `src/prompt_templates.py` | Brand-safe prompt templates per content type |
| `src/llm_integration.py` | OpenAI API calls and provider error handling |
| `src/feedback_repository.py` | Feedback persistence boundary, currently file-backed |
| `src/content_artifacts.py` | Backend artifact helpers such as comparison and DOCX export |
| `frontend/` | Production Next.js interface |

## Feedback Loop

The frontend includes a feedback loop for generated drafts:

- approve a generated draft
- mark it as needing revision
- add reviewer comments
- regenerate using the reviewer feedback and previous draft

The current backend stores feedback as append-only JSONL in `feedback/generation_feedback.jsonl`.
The persistence layer is isolated in `src/feedback_repository.py` so it can be replaced with Supabase later.

See [docs/feedback_loop.md](docs/feedback_loop.md) for the current flow and the planned Supabase-ready architecture.

## Setup

```bash
cd ai-content-creator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI key to `.env`:

```bash
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

## Run Locally

Terminal 1, Python API:

```bash
uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, Next.js frontend:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open the Next.js URL shown in the terminal, usually `http://localhost:3000`.
The frontend calls local `/api/*` routes, which proxy to `PYTHON_API_BASE_URL`.

## API Endpoints

- `GET /health`
- `POST /generate`
- `POST /upload`
- `POST /feedback`
- `POST /chat`
- `POST /chat/stream`
- `POST /compare`
- `POST /export/docx`

## CLI

The CLI still uses the same backend pipeline logic:

```bash
python main.py --type blog --topic "AI Ethics at SRH"
python main.py --type social --topic "Open Day June 2026" --extra "Join us 14 June in Berlin"
python main.py --type program --topic "MSc Applied Data Science and AI"
python main.py --type newsletter --topic "April Campus Updates"
```

## Project Structure

```txt
ai-content-creator/
├── api_server.py
├── app.py
├── frontend/
├── src/
├── docs/
├── knowledge_base/
│   ├── primary/
│   └── secondary/
├── examples/
├── requirements.txt
└── README.md
```
