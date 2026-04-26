# ContentForge-AI

Local-first AI-powered YouTube automation platform with modular multi-agent architecture.

## What it does

You submit a video idea. A pipeline of AI agents research trends, expand ideas, write scripts, validate quality, optimize for SEO, and generate media prompts — producing everything needed for faceless YouTube content.

## Pipeline

```
Idea → Research → Ideation → Script → Validation → Optimization → Media → Human Approval
```

Each agent communicates via structured JSON, with retry + feedback loops.

## Stack

- **Backend**: FastAPI (Python)
- **Orchestration**: LangGraph (`StateGraph`) — parallel/fan-out nodes drop in as the pipeline grows
- **Frontend**: Streamlit (Phase 1; React-ready)
- **DB**: SQLite
- **LLM**: Gemini (`gemini-flash-latest`) and Claude (`claude-opus-4-7`) both built in via a pluggable `LLMManager`. Pick the default with `LLM_PROVIDER` in `.env`; register additional providers in `backend/services/llm/`
- **Scraping**: Firecrawl
- **Output**: video script (Markdown), voiceover narration (plain text), scene breakdown with visual prompts (JSON) — ready to paste into any TTS or video-gen tool you choose

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in API keys

# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
streamlit run frontend/app.py
```

Open:
- API docs: http://localhost:8000/docs
- UI: http://localhost:8501

## Structure

```
backend/
  agents/          # Research, Ideation, Script, Validation, Optimization, Media
  orchestrator/    # Sequential + iterative pipeline with feedback loops
  services/        # LLM provider, Firecrawl, TTS, Video adapters
  schemas/         # Pydantic models (agent I/O contracts)
  routes/          # FastAPI endpoints
  workers/         # Background trends researcher
  prompts/         # Agent system prompts (editable markdown)
frontend/          # Streamlit multipage app
examples/          # Sample workflow output
```

## API

| Method | Path                | Purpose                          |
|--------|---------------------|----------------------------------|
| POST   | `/idea/submit`      | Kick off pipeline for a new idea |
| GET    | `/agents/status`    | Poll pipeline run state + logs   |
| POST   | `/generate/final`   | Generate media assets on approval|
| GET    | `/trends`           | Latest scraped trend insights    |

## Extending

Add a new agent: drop a file in `backend/agents/`, inherit from `BaseAgent`, register in `AGENTS_REGISTRY` in `orchestrator/pipeline.py`, and add edges in `build_graph()`. Parallel agents = multiple `add_edge` calls from the same source node.

Add another LLM provider: subclass `BaseLLMProvider` in `backend/services/llm/`, then register it with `get_llm_manager().register(MyProvider(...))`. Switch the default via `LLM_PROVIDER` in `.env`. Claude is hardcoded and registered on startup.

Niche config: edit prompts in `backend/prompts/*.md`.
