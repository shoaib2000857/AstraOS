from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db, services
from ..schemas import ChatRequest, ChatResponse, ConversationRead

router = APIRouter(prefix="/api/chat")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db_sess: Session = Depends(get_db)):
    # Ensure conversation exists or create
    if req.conversation_id is None:
        conv = db.models.Conversation(title=None)
        db_sess.add(conv)
        db_sess.commit()
        db_sess.refresh(conv)
    else:
        conv = db_sess.query(db.models.Conversation).filter_by(id=req.conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # persist user message
    user_msg = db.models.Message(conversation_id=conv.id, role="user", content=req.prompt)
    db_sess.add(user_msg)
    db_sess.commit()
    db_sess.refresh(user_msg)

    # Call Ollama
    client = services.llm.OllamaClient()
    try:
        resp = client.chat(req.model, req.prompt)
        # This assumes the response contains a top-level `text` or `choices` -> adapt per Ollama API
        reply_text = None
        if isinstance(resp, dict):
            if "text" in resp:
                reply_text = resp["text"]
            elif "choices" in resp and len(resp["choices"]) > 0:
                reply_text = resp["choices"][0].get("text") or resp["choices"][0].get("message", {}).get("content")
        if reply_text is None:
            reply_text = str(resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # persist assistant message
    assistant_msg = db.models.Message(conversation_id=conv.id, role="assistant", content=reply_text)
    db_sess.add(assistant_msg)
    db_sess.commit()
    db_sess.refresh(assistant_msg)

    return ChatResponse(reply=reply_text, conversation_id=conv.id, message_id=assistant_msg.id)
