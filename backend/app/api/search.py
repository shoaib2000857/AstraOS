from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..services import llm, qdrant

router = APIRouter(prefix="/api/search")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    embedding_model: str | None = None


@router.post("/", response_model=list[dict])
def search(req: SearchRequest, db_sess: Session = Depends(get_db)):
    if not req.query:
        raise HTTPException(status_code=400, detail="query required")

    model = req.embedding_model or "text-embedding-3-small"
    client = llm.OllamaClient()
    embeddings = client.embed_text(model, [req.query])
    if not embeddings or not embeddings[0]:
        raise HTTPException(status_code=500, detail="failed to compute embedding")
    query_vec = embeddings[0]

    try:
        hits = qdrant.search(collection="documents", query_vector=query_vec, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qdrant search error: {e}")

    results = []
    for h in hits:
        payload = h.payload if hasattr(h, 'payload') else getattr(h, 'payload', None)
        results.append({
            "id": h.id,
            "score": getattr(h, 'score', None),
            "payload": payload,
        })

    return results
