from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import db
from ..services.memory_service import save_memory

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


class MemoryUpdate(BaseModel):
    text: str
    category: str = "profile"
    source: str | None = None


def serialize_memory(memory):
    return {
        "id": memory.id,
        "text": memory.text,
        "category": memory.category,
        "source": memory.source,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at,
    }


@router.post("/", response_model=dict)
def create_memory(payload: MemoryCreate, db_sess: Session = Depends(get_db)):
    memory = save_memory(db_sess, text=payload.text, category=payload.category, source=payload.source)
    return serialize_memory(memory)


@router.get("/", response_model=list[dict])
def list_memories(limit: int = 50, db_sess: Session = Depends(get_db)):
    items = db_sess.query(db.models.Memory).order_by(db.models.Memory.updated_at.desc()).limit(limit).all()
    return [serialize_memory(item) for item in items]


@router.get("/{memory_id}", response_model=dict)
def get_memory(memory_id: int, db_sess: Session = Depends(get_db)):
    memory = db_sess.query(db.models.Memory).filter_by(id=memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return serialize_memory(memory)


@router.put("/{memory_id}", response_model=dict)
def update_memory(memory_id: int, payload: MemoryUpdate, db_sess: Session = Depends(get_db)):
    memory = db_sess.query(db.models.Memory).filter_by(id=memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.text = payload.text.strip()
    memory.category = payload.category
    memory.source = payload.source
    db_sess.add(memory)
    db_sess.commit()
    db_sess.refresh(memory)
    return serialize_memory(memory)


@router.delete("/{memory_id}", response_model=dict)
def delete_memory(memory_id: int, db_sess: Session = Depends(get_db)):
    memory = db_sess.query(db.models.Memory).filter_by(id=memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db_sess.delete(memory)
    db_sess.commit()
    return {"status": "deleted"}
