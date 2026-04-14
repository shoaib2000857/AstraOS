from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db, services
from ..schemas import ChatRequest, ChatResponse, ConversationRead
from fastapi.responses import StreamingResponse
import json
import asyncio

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


@router.post("/stream")
async def chat_stream(req: ChatRequest, db_sess: Session = Depends(get_db)):
    # Setup conversation
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

    client = services.llm.OllamaClient()

    async def event_generator():
        # Stream pieces from the model and yield SSE-formatted chunks
        try:
            async for piece in client.chat_stream(req.model, req.prompt):
                # Each piece is plain text; send as JSON payload in data field
                payload = {"type": "delta", "text": piece}
                yield f"data: {json.dumps(payload)}\n\n"
            # After stream complete, persist assembled assistant message
            # Note: we don't have full assembly here; for simplicity, fetch full reply once
            loop = asyncio.get_event_loop()
            full = await loop.run_in_executor(None, client.chat, req.model, req.prompt)
            reply_text = None
            if isinstance(full, dict):
                if "text" in full:
                    reply_text = full["text"]
                elif "choices" in full and len(full["choices"]) > 0:
                    reply_text = full["choices"][0].get("text") or full["choices"][0].get("message", {}).get("content")
            if reply_text is None:
                reply_text = str(full)

            assistant_msg = db.models.Message(conversation_id=conv.id, role="assistant", content=reply_text)
            db_sess.add(assistant_msg)
            db_sess.commit()
            db_sess.refresh(assistant_msg)

            yield f"data: {json.dumps({"type": "done", "message_id": assistant_msg.id, "text": reply_text})}\n\n"
        except Exception as e:
            err = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')
