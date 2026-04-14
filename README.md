# AstraOS — Memory-Augmented Personal AI OS

Prototype workspace for a privacy-first, desktop-native personal AI with persistent memory, file-grounded QA, and local LLMs.

Architecture (MVP):
- Frontend: Tauri + React + TypeScript
- Backend: FastAPI (Python)
- LLMs: Ollama (local)
- Vector DB: Qdrant (local)
- Storage: SQLite for structured data

Goals: quick local chat, memory save/recall, file ingestion + semantic search.

Quick start (backend):

1. Create a Python venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Run backend:

```bash
uvicorn backend.app.main:app --reload
```

See `backend/.env.example` to configure `OLLAMA_URL` and `QDRANT_URL`.

Local development (recommended):

1. Start Qdrant (Docker):

```bash
cd docker
docker-compose up -d
```

2. Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

3. Frontend:

```bash
cd apps/desktop
./start.sh
```

Run tests:

```bash
cd backend
pytest -q
```

What's included:

- FastAPI backend: health, chat (sync + streaming), conversation and memory APIs, ingestion and Qdrant indexing hooks.
- React + Vite frontend with a minimal chat UI that streams responses.
- Docker compose for Qdrant in `/docker`.

Next recommended steps: configure Ollama locally (set `OLLAMA_URL`), iterate on prompts and memory retention policies, and add UI pages for memory/document inspection.