import hashlib
from pathlib import Path
from typing import List

from .llm_service import DEFAULT_EMBEDDING_MODEL, OllamaClient
from .qdrant_service import ensure_collection, is_available, upsert_vectors


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= length:
            break
        start = end - overlap
    return chunks


def summarize_text(text: str, max_chars: int = 320) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def checksum_bytes(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def read_document_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    raw = path.read_bytes()

    if suffix in {".txt", ".md", ".py", ".json", ".ts", ".tsx", ".js", ".jsx", ".csv"}:
        return raw.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            import fitz

            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n\n".join(page.get_text() for page in doc)
        except Exception:
            return ""
    return raw.decode("utf-8", errors="ignore")


def embed_and_index_document(
    db_session,
    models,
    document_obj,
    source_text: str | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    collection_name: str = "documents",
):
    text = source_text if source_text is not None else read_document_text(document_obj.file_path)
    text_chunks = chunk_text(text)

    existing = db_session.query(models.DocumentChunk).filter_by(document_id=document_obj.id).all()
    for chunk in existing:
        db_session.delete(chunk)
    db_session.commit()

    created_chunks = []
    for index, chunk_value in enumerate(text_chunks):
        chunk = models.DocumentChunk(
            document_id=document_obj.id,
            chunk_text=chunk_value,
            chunk_index=index,
            chunk_metadata={
                "document_id": document_obj.id,
                "chunk_index": index,
                "title": document_obj.title,
                "source": document_obj.file_path,
            },
        )
        db_session.add(chunk)
        created_chunks.append(chunk)

    document_obj.summary = summarize_text(text)
    db_session.add(document_obj)
    db_session.commit()

    if not text_chunks:
        return {"status": "no_text", "chunks": 0}

    embeddings = OllamaClient().embed_text(embedding_model, text_chunks)
    if not embeddings or not embeddings[0] or not is_available():
        return {"status": "chunks_created", "chunks": len(text_chunks), "search_mode": "lexical"}

    try:
        ensure_collection(collection_name, len(embeddings[0]))
        vectors = []
        for index, embedding in enumerate(embeddings):
            vector_id = f"{document_obj.id}-{index}"
            vectors.append(
                (
                    vector_id,
                    embedding,
                    {
                        "document_id": document_obj.id,
                        "chunk_index": index,
                        "title": document_obj.title,
                        "source": document_obj.file_path,
                        "text": text_chunks[index],
                    },
                )
            )

        upsert_vectors(collection_name, vectors)
        for index, chunk in enumerate(created_chunks):
            chunk.vector_id = f"{document_obj.id}-{index}"
            db_session.add(chunk)
        db_session.commit()
    except Exception:
        return {"status": "chunks_created", "chunks": len(text_chunks), "search_mode": "lexical"}

    return {"status": "indexed", "chunks": len(text_chunks), "search_mode": "vector"}
