from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from .. import db
from ..db import PROJECT_ROOT
from ..services.ingest_service import checksum_bytes, embed_and_index_document

router = APIRouter(prefix="/api/ingest")


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db_sess: Session = Depends(get_db)):
    uploads_dir = PROJECT_ROOT / "storage" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename or "upload").name
    stored_name = f"{uuid4().hex}_{original_name}"
    target_path = uploads_dir / stored_name
    content = await file.read()
    target_path.write_bytes(content)

    text = None
    suffix = target_path.suffix.lower()
    if file.content_type == "text/plain" or suffix in {".txt", ".md", ".py", ".ts", ".tsx", ".js", ".json", ".csv"}:
        text = content.decode("utf-8", errors="ignore")
    elif suffix == ".pdf":
        try:
            import fitz

            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n\n".join(page.get_text() for page in doc)
        except Exception:
            text = None

    document = db.models.Document(
        title=original_name,
        file_path=str(target_path),
        file_type=file.content_type or suffix.lstrip("."),
        checksum=checksum_bytes(content),
    )
    db_sess.add(document)
    db_sess.commit()
    db_sess.refresh(document)

    if text is not None:
        indexing = embed_and_index_document(db_sess, db.models, document, source_text=text)
    else:
        indexing = embed_and_index_document(db_sess, db.models, document)

    return {
        "status": "uploaded",
        "path": str(target_path),
        "document_id": document.id,
        "summary": document.summary,
        "indexing": indexing,
    }
