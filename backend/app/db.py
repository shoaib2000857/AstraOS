import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "storage" / "sqlite" / "app.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

models = None


def ensure_storage_dirs():
    if DATABASE_URL.startswith("sqlite"):
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_models():
    global models
    if models is None:
        from . import models as imported_models

        models = imported_models
    return models


def init_db():
    ensure_storage_dirs()
    load_models()
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DATABASE_URL}")
