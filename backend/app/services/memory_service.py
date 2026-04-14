import re
from datetime import datetime
from typing import List

WORD_RE = re.compile(r"[a-zA-Z0-9']+")
MEMORY_PATTERNS = [
    ("preference", re.compile(r"\b(i prefer|i like|please use|my preferred)\b", re.IGNORECASE)),
    ("project", re.compile(r"\b(my project is|i am building|i'm building|i am working on|i'm working on)\b", re.IGNORECASE)),
    ("profile", re.compile(r"\b(i am|i'm|my name is|i study|i work as)\b", re.IGNORECASE)),
    ("deadline", re.compile(r"\b(due|deadline|exam|interview|next week|tomorrow)\b", re.IGNORECASE)),
]


def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text)}


def classify_memory(text: str) -> str:
    for category, pattern in MEMORY_PATTERNS:
        if pattern.search(text):
            return category
    return "profile"


def save_memory(
    db_session,
    text: str,
    category: str = "profile",
    source: str | None = None,
    confidence: float | None = None,
):
    from .. import db

    normalized = normalize(text)
    existing_memories = db_session.query(db.models.Memory).all()
    for existing in existing_memories:
        if normalize(existing.text) == normalized:
            existing.category = category or existing.category
            existing.source = source or existing.source
            existing.confidence = confidence if confidence is not None else existing.confidence
            existing.updated_at = datetime.utcnow()
            db_session.add(existing)
            db_session.commit()
            db_session.refresh(existing)
            return existing

    created = db.models.Memory(
        text=text.strip(),
        category=category or classify_memory(text),
        source=source,
        confidence=confidence,
    )
    db_session.add(created)
    db_session.commit()
    db_session.refresh(created)
    return created


def extract_candidate_memories(text: str) -> list[dict]:
    candidates: list[dict] = []
    content = text.strip()
    if not content:
        return candidates

    explicit = re.search(r"\bremember(?: that)?\s+(.+)$", content, re.IGNORECASE)
    if explicit:
        remembered = explicit.group(1).strip().rstrip(".")
        if remembered:
            candidates.append({"text": remembered, "category": classify_memory(remembered), "confidence": 0.95})

    for sentence in re.split(r"(?<=[.!?])\s+", content):
        sentence = sentence.strip().rstrip(".")
        if len(sentence) < 12 or len(sentence) > 220:
            continue
        if sentence.lower().startswith("remember "):
            continue
        category = classify_memory(sentence)
        if category == "profile" and not re.search(r"\b(i am|i'm|my|i )\b", sentence, re.IGNORECASE):
            continue
        if any(item["text"].lower() == sentence.lower() for item in candidates):
            continue
        candidates.append({"text": sentence, "category": category, "confidence": 0.65})

    return candidates[:5]


def capture_memories_from_text(db_session, text: str, source: str | None = None):
    stored = []
    for candidate in extract_candidate_memories(text):
        stored.append(
            save_memory(
                db_session,
                text=candidate["text"],
                category=candidate["category"],
                source=source,
                confidence=candidate["confidence"],
            )
        )
    return stored


def find_memories(db_session, query: str, top_k: int = 5) -> List[dict]:
    from .. import db

    query_tokens = tokenize(query)
    ranked = []
    for memory in db_session.query(db.models.Memory).all():
        text_tokens = tokenize(memory.text)
        overlap = len(query_tokens & text_tokens)
        score = overlap / len(query_tokens) if query_tokens else 0.0
        if query.lower() in memory.text.lower():
            score += 1.0
        if score > 0:
            ranked.append(
                {
                    "id": memory.id,
                    "text": memory.text,
                    "category": memory.category,
                    "source": memory.source,
                    "created_at": memory.created_at,
                    "score": score,
                }
            )

    if not ranked:
        recent = (
            db_session.query(db.models.Memory)
            .order_by(db.models.Memory.updated_at.desc(), db.models.Memory.created_at.desc())
            .limit(top_k)
            .all()
        )
        return [
            {
                "id": memory.id,
                "text": memory.text,
                "category": memory.category,
                "source": memory.source,
                "created_at": memory.created_at,
                "score": 0.0,
            }
            for memory in recent
        ]

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_k]
