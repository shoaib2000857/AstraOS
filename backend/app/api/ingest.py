from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db
import os

router = APIRouter(prefix="/api/ingest")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db_sess: Session = Depends(get_db)):
    # Save uploaded file to storage/uploads
    uploads_dir = os.path.join(os.getcwd(), "storage", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    target_path = os.path.join(uploads_dir, file.filename)
    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Try to extract text from simple types; PDF support via PyMuPDF if available
    text = None
    if file.content_type == "text/plain" or file.filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    elif file.filename.endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            pages = []
            for page in doc:
                pages.append(page.get_text())
            text = "\n\n".join(pages)
        except Exception:
            text = None

    # Create document record
    doc = db.models.Document(title=file.filename, file_path=target_path, file_type=file.content_type)
    db_sess.add(doc)
    db_sess.commit()
    db_sess.refresh(doc)

    # Optionally, chunk and store DocumentChunk rows here (placeholder)
    if text:
        chunk = db.models.DocumentChunk(document_id=doc.id, chunk_text=text[:4000], chunk_index=0)
        db_sess.add(chunk)
        db_sess.commit()

    return {"status": "uploaded", "path": target_path, "document_id": doc.id}
