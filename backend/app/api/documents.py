from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db

router = APIRouter(prefix="/api/documents")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.get("/")
def list_documents(db_sess: Session = Depends(get_db)):
    docs = db_sess.query(db.models.Document).order_by(db.models.Document.imported_at.desc()).all()
    return [
        {
            "id": document.id,
            "title": document.title,
            "file_path": document.file_path,
            "summary": document.summary,
            "checksum": document.checksum,
            "imported_at": document.imported_at,
            "chunk_count": len(document.chunks),
        }
        for document in docs
    ]


@router.get("/{doc_id}")
def get_document(doc_id: int, db_sess: Session = Depends(get_db)):
    document = db_sess.query(db.models.Document).filter_by(id=doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = (
        db_sess.query(db.models.DocumentChunk)
        .filter_by(document_id=document.id)
        .order_by(db.models.DocumentChunk.chunk_index)
        .all()
    )
    return {
        "id": document.id,
        "title": document.title,
        "file_path": document.file_path,
        "summary": document.summary,
        "checksum": document.checksum,
        "chunks": [
            {"id": chunk.id, "index": chunk.chunk_index, "text": chunk.chunk_text, "vector_id": chunk.vector_id}
            for chunk in chunks
        ],
    }


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db_sess: Session = Depends(get_db)):
    document = db_sess.query(db.models.Document).filter_by(id=doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = Path(document.file_path)
    db_sess.delete(document)
    db_sess.commit()
    if file_path.exists():
        file_path.unlink()
    return {"status": "deleted"}
