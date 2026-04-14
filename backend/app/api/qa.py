from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import db
from ..services import llm, memory
from ..services.retrieval_service import search_document_chunks

router = APIRouter(prefix="/api/qa")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


class QARequest(BaseModel):
    question: str
    top_k: int = 5
    embedding_model: str | None = None
    conversation_id: int | None = None


@router.post("/answer")
def answer(req: QARequest, db_sess: Session = Depends(get_db)):
    if not req.question:
        raise HTTPException(status_code=400, detail="question required")

    client = llm.OllamaClient()
    sources = search_document_chunks(
        db_session=db_sess,
        models=db.models,
        query=req.question,
        top_k=req.top_k,
        embedding_model=req.embedding_model,
    )
    contexts = [item["text"] for item in sources if item.get("text")]

    memories = memory.find_memories(db_sess, req.question, top_k=5)
    if req.conversation_id:
        conv = db_sess.query(db.models.Conversation).filter_by(id=req.conversation_id).first()
        if conv:
            recent = "\n".join(f"{message.role}: {message.content}" for message in conv.messages[-10:])
            memories.insert(0, {"id": "recent", "text": recent, "category": "recent_messages", "score": 1.0})

    prompt_parts = []
    if memories:
        prompt_parts.append(
            "Relevant memories:\n" + "\n\n".join([f"[{item['category']}] {item['text']}" for item in memories])
        )
    if contexts:
        prompt_parts.append("Relevant documents:\n" + "\n\n".join(contexts))
    prompt_parts.append("Question:\n" + req.question)
    prompt = "\n\n---\n\n".join(prompt_parts)

    try:
        reply = client.chat(None, prompt)
        answer_text = client.extract_text(reply) or str(reply)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM error: {exc}")

    return {"answer": answer_text, "sources": sources, "memories_used": len(memories)}
