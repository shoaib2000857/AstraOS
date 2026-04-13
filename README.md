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

Next steps: scaffold Tauri app, add Ollama connector, implement ingestion pipeline, and Qdrant indexing.