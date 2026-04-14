from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import health
from .api import chat
from .api import conversations, memory, ingest
from .api import search

app = FastAPI(title="AstraOS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(memory.router)
app.include_router(ingest.router)
app.include_router(search.router)

@app.get("/ready")
async def ready():
    return {"status": "ready"}
