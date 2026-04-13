import math
from typing import List
from .llm_service import OllamaClient
from .qdrant_service import ensure_collection, upsert_vectors
from .. import db


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


def embed_and_index_document(db_session, document_obj, embedding_model: str = "text-embedding-3-small", collection_name: str = "documents"):
    """Chunk a document, request embeddings, upsert to Qdrant, and update DB chunk records with vector ids.

    - `document_obj` is an instance of `db.models.Document` (already persisted)
    - This function will create DocumentChunk rows if not present for the provided text chunks.
    """
    # Read existing chunks; if none, assume the document file exists and was saved earlier
    existing = db_session.query(db.models.DocumentChunk).filter_by(document_id=document_obj.id).all()
    if existing:
        text_chunks = [c.chunk_text for c in existing]
    else:
        # Try loading file contents
        try:
            with open(document_obj.file_path, "rb") as f:
                raw = f.read()
                text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
        text_chunks = chunk_text(text)
        # create chunk rows
        for i, t in enumerate(text_chunks):
            c = db.models.DocumentChunk(document_id=document_obj.id, chunk_text=t, chunk_index=i)
            db_session.add(c)
        db_session.commit()
        existing = db_session.query(db.models.DocumentChunk).filter_by(document_id=document_obj.id).order_by(db.models.DocumentChunk.chunk_index).all()
        text_chunks = [c.chunk_text for c in existing]

    if not text_chunks:
        return {"status": "no_chunks"}

    # Get embeddings
    client = OllamaClient()
    embeddings = client.embed_text(embedding_model, text_chunks)
    if not embeddings:
        return {"status": "no_embeddings"}

    # Ensure qdrant collection
    vector_size = len(embeddings[0])
    ensure_collection(collection_name, vector_size)

    # Prepare upsert tuples (id, vector, payload)
    vectors = []
    for i, emb in enumerate(embeddings):
        vec_id = f"{document_obj.id}-{i}"
        payload = {
            "document_id": document_obj.id,
            "chunk_index": i,
            "text": (text_chunks[i][:1000] if len(text_chunks[i]) > 1000 else text_chunks[i]),
            "source": document_obj.file_path,
        }
        vectors.append((vec_id, emb, payload))

    upsert_vectors(collection_name, vectors)

    # Update DocumentChunk.vector_id fields
    for i, chunk_row in enumerate(existing):
        chunk_row.vector_id = f"{document_obj.id}-{i}"
        db_session.add(chunk_row)
    db_session.commit()

    return {"status": "indexed", "chunks": len(embeddings)}
