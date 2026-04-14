from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db
from ..services.task_service import extract_tasks_from_text

router = APIRouter(prefix="/api/tasks")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.post("/from_conversation/{conv_id}")
def extract_from_conversation(conv_id: int, db_sess: Session = Depends(get_db)):
    conv = db_sess.query(db.models.Conversation).filter_by(id=conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    text = "\n".join([m.content for m in conv.messages])
    tasks = extract_tasks_from_text(text)
    return {"conversation_id": conv_id, "tasks": tasks}


@router.post("/from_document/{doc_id}")
def extract_from_document(doc_id: int, db_sess: Session = Depends(get_db)):
    doc = db_sess.query(db.models.Document).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db_sess.query(db.models.DocumentChunk).filter_by(document_id=doc.id).all()
    text = "\n".join([c.chunk_text for c in chunks])
    tasks = extract_tasks_from_text(text)
    return {"document_id": doc_id, "tasks": tasks}
