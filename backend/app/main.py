from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import db
from .api import health
from .api import chat
from .api import conversations, memory, ingest
from .api import search
from .api import documents
from .api import tasks
from .api import qa

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="AstraOS Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
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
app.include_router(documents.router)
app.include_router(tasks.router)
app.include_router(qa.router)

@app.get("/ready")
async def ready():
    return {"status": "ready"}
