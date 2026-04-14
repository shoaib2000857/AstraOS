import math
import re

from . import qdrant_service
from .llm_service import DEFAULT_EMBEDDING_MODEL, OllamaClient

WORD_RE = re.compile(r"[a-zA-Z0-9']+")


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text)}


def lexical_score(query: str, text: str, title: str | None = None) -> float:
    if not text:
        return 0.0
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0

    overlap = len(query_tokens & text_tokens)
    if overlap == 0:
        return 0.0

    score = overlap / math.sqrt(len(query_tokens) * len(text_tokens))
    lowered_query = query.lower()
    if lowered_query in text.lower():
        score += 0.75
    if title and lowered_query in title.lower():
        score += 0.25
    return score


def lexical_search_document_chunks(db_session, models, query: str, top_k: int = 5):
    ranked = []
    chunks = db_session.query(models.DocumentChunk).all()
    for chunk in chunks:
        title = chunk.document.title if chunk.document else None
        score = lexical_score(query, chunk.chunk_text, title=title)
        if score <= 0:
            continue
        ranked.append(
            {
                "id": chunk.vector_id or chunk.id,
                "score": score,
                "document_id": chunk.document_id,
                "title": title,
                "text": chunk.chunk_text,
                "payload": {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "source": chunk.document.file_path if chunk.document else None,
                    "title": title,
                    "text": chunk.chunk_text,
                },
                "search_mode": "lexical",
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_k]


def vector_search_document_chunks(query: str, top_k: int = 5, embedding_model: str | None = None):
    if not qdrant_service.is_available():
        return []

    try:
        embeddings = OllamaClient().embed_text(embedding_model or DEFAULT_EMBEDDING_MODEL, [query])
    except Exception:
        return []

    if not embeddings or not embeddings[0]:
        return []

    try:
        hits = qdrant_service.search(collection="documents", query_vector=embeddings[0], top_k=top_k)
    except Exception:
        return []

    results = []
    for hit in hits:
        payload = hit.payload if hasattr(hit, "payload") else getattr(hit, "payload", None) or {}
        results.append(
            {
                "id": hit.id,
                "score": getattr(hit, "score", None),
                "document_id": payload.get("document_id"),
                "title": payload.get("title"),
                "text": payload.get("text"),
                "payload": payload,
                "search_mode": "vector",
            }
        )
    return results


def search_document_chunks(db_session, models, query: str, top_k: int = 5, embedding_model: str | None = None):
    vector_results = vector_search_document_chunks(query=query, top_k=top_k, embedding_model=embedding_model)
    if vector_results:
        return vector_results
    return lexical_search_document_chunks(db_session=db_session, models=models, query=query, top_k=top_k)
