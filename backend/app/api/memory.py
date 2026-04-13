from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db
from ..schemas import MessageRead
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/memories")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


class MemoryCreate(BaseModel):
    text: str
    category: str = "profile"
    source: str | None = None


@router.post("/", response_model=dict)
def create_memory(payload: MemoryCreate, db_sess: Session = Depends(get_db)):
    mem = db.models.Memory(text=payload.text, category=payload.category, source=payload.source)
    db_sess.add(mem)
    db_sess.commit()
    db_sess.refresh(mem)
    return {"id": mem.id, "text": mem.text, "category": mem.category, "created_at": mem.created_at}


@router.get("/", response_model=list[dict])
def list_memories(limit: int = 50, db_sess: Session = Depends(get_db)):
    items = db_sess.query(db.models.Memory).order_by(db.models.Memory.created_at.desc()).limit(limit).all()
    return [{"id": m.id, "text": m.text, "category": m.category, "created_at": m.created_at} for m in items]


@router.get("/{memory_id}", response_model=dict)
def get_memory(memory_id: int, db_sess: Session = Depends(get_db)):
    m = db_sess.query(db.models.Memory).filter_by(id=memory_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"id": m.id, "text": m.text, "category": m.category, "created_at": m.created_at}


@router.delete("/{memory_id}", response_model=dict)
def delete_memory(memory_id: int, db_sess: Session = Depends(get_db)):
    m = db_sess.query(db.models.Memory).filter_by(id=memory_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Memory not found")
    db_sess.delete(m)
    db_sess.commit()
    return {"status": "deleted"}
