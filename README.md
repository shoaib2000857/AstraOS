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

Recommended Python: 3.11+ (the backend now works cleanly on Python 3.13 as well). If you use Conda it's easiest to create an isolated environment.

Option A — Conda (recommended):

```bash
conda create -n astraos-py311 python=3.11 -y
conda activate astraos-py311
cd backend
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```


Run backend:

```bash
cd backend
./start.sh
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

- FastAPI backend: health, chat (sync + streaming), conversation/memory/document/task APIs, file ingestion, lexical fallback retrieval, and Qdrant hooks.
- React + Vite frontend with conversation history, editable memories, document upload/inspection, and grounded Q&A screens.
- Docker compose for Qdrant in `/docker`.

Next recommended steps: configure Ollama locally (set `OLLAMA_URL`), iterate on prompts and memory retention policies, and add UI pages for memory/document inspection.
