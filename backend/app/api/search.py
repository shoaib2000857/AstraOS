from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..services.retrieval_service import search_document_chunks

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

    return search_document_chunks(
        db_session=db_sess,
        models=db.models,
        query=req.query,
        top_k=req.top_k,
        embedding_model=req.embedding_model,
    )
