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

    # If we extracted text, create chunks and index them into Qdrant
    if text:
        from ..services.ingest_service import embed_and_index_document
        # create a placeholder chunk row; embed_and_index_document will create/manage chunks
        res = embed_and_index_document(db_sess, doc)
    else:
        res = {"status": "uploaded_no_text"}

    return {"status": "uploaded", "path": target_path, "document_id": doc.id, "indexing": res}
