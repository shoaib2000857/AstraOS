import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import db, services
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat")
MAX_HISTORY_MESSAGES = 12
MAX_MEMORY_ITEMS = 5


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def conversation_title(prompt: str) -> str:
    title = " ".join(prompt.strip().split())
    return title[:80] or "New conversation"


def touch_conversation(conversation):
    conversation.updated_at = datetime.utcnow()


def fetch_conversation_messages(db_sess: Session, conversation_id: int):
    return (
        db_sess.query(db.models.Message)
        .filter_by(conversation_id=conversation_id)
        .order_by(db.models.Message.timestamp.asc(), db.models.Message.id.asc())
        .all()
    )


def build_model_messages(db_sess: Session, conversation_id: int, prompt: str):
    history = fetch_conversation_messages(db_sess, conversation_id)[-MAX_HISTORY_MESSAGES:]
    relevant_memories = services.memory.find_memories(db_sess, prompt, top_k=MAX_MEMORY_ITEMS)

    system_parts = [
        "You are AstraOS, a privacy-first personal AI workspace assistant.",
        "Use the available conversation history and remembered user context when it is relevant.",
        "If context is insufficient, say so plainly instead of inventing details.",
    ]
    if relevant_memories:
        memory_lines = [f"- [{item['category']}] {item['text']}" for item in relevant_memories]
        system_parts.append("Relevant long-term memories:\n" + "\n".join(memory_lines))

    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for message in history:
        messages.append({"role": message.role, "content": message.content})

    return messages, relevant_memories


def extract_reply_text(payload):
    return services.llm.OllamaClient.extract_text(payload) or str(payload)


def ensure_conversation(db_sess: Session, conversation_id: int | None):
    if conversation_id is None:
        conv = db.models.Conversation(title=None)
        db_sess.add(conv)
        db_sess.commit()
        db_sess.refresh(conv)
        return conv

    conv = db_sess.query(db.models.Conversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def persist_user_message(db_sess: Session, conv, prompt: str):
    user_msg = db.models.Message(conversation_id=conv.id, role="user", content=prompt)
    db_sess.add(user_msg)
    if not conv.title:
        conv.title = conversation_title(prompt)
    touch_conversation(conv)
    db_sess.commit()
    db_sess.refresh(user_msg)

    services.memory.capture_memories_from_text(
        db_sess,
        prompt,
        source=f"conversation:{conv.id}:message:{user_msg.id}",
    )
    return user_msg


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db_sess: Session = Depends(get_db)):
    conv = ensure_conversation(db_sess, req.conversation_id)
    persist_user_message(db_sess, conv, req.prompt)

    client = services.llm.OllamaClient()
    model_messages, _ = build_model_messages(db_sess, conv.id, req.prompt)
    try:
        response = client.chat_messages(req.model, model_messages)
        reply_text = extract_reply_text(response)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM error: {exc}")

    assistant_msg = db.models.Message(conversation_id=conv.id, role="assistant", content=reply_text)
    db_sess.add(assistant_msg)
    touch_conversation(conv)
    db_sess.commit()
    db_sess.refresh(assistant_msg)

    return ChatResponse(reply=reply_text, conversation_id=conv.id, message_id=assistant_msg.id)


@router.post("/stream")
async def chat_stream(req: ChatRequest, db_sess: Session = Depends(get_db)):
    conv = ensure_conversation(db_sess, req.conversation_id)
    persist_user_message(db_sess, conv, req.prompt)

    client = services.llm.OllamaClient()
    model_messages, relevant_memories = build_model_messages(db_sess, conv.id, req.prompt)

    async def event_generator():
        assembled = ""
        try:
            async for piece in client.chat_stream_messages(req.model, model_messages):
                assembled += piece
                yield f"data: {json.dumps({'type': 'delta', 'text': piece})}\n\n"

            reply_text = assembled.strip()
            if not reply_text:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, client.chat_messages, req.model, model_messages)
                reply_text = extract_reply_text(response)

            assistant_msg = db.models.Message(conversation_id=conv.id, role="assistant", content=reply_text)
            db_sess.add(assistant_msg)
            touch_conversation(conv)
            db_sess.commit()
            db_sess.refresh(assistant_msg)

            final_payload = {
                "type": "done",
                "message_id": assistant_msg.id,
                "conversation_id": conv.id,
                "text": reply_text,
                "memories_used": len(relevant_memories),
            }
            yield f"data: {json.dumps(final_payload)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
