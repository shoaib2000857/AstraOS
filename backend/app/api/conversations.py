from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db
from ..schemas import ConversationCreate, ConversationRead

router = APIRouter(prefix="/api/conversations")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.post("/", response_model=ConversationRead)
def create_conversation(payload: ConversationCreate, db_sess: Session = Depends(get_db)):
    conv = db.models.Conversation(title=payload.title)
    db_sess.add(conv)
    db_sess.commit()
    db_sess.refresh(conv)
    return conv


@router.get("/", response_model=list[ConversationRead])
def list_conversations(db_sess: Session = Depends(get_db)):
    items = db_sess.query(db.models.Conversation).order_by(db.models.Conversation.updated_at.desc()).all()
    return items


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: int, db_sess: Session = Depends(get_db)):
    conv = db_sess.query(db.models.Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}", response_model=dict)
def delete_conversation(conversation_id: int, db_sess: Session = Depends(get_db)):
    conv = db_sess.query(db.models.Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db_sess.delete(conv)
    db_sess.commit()
    return {"status": "deleted"}
