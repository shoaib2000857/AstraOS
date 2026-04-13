from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/sqlite/app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from .models import Conversation, Message  # noqa: F401
    Base.metadata.create_all(bind=engine)


# Import models at module load so other modules can reference `db.models`.
# Models import `Base` from this module, so this must come after Base is defined.
try:
    from . import models  # noqa: F401
except Exception:
    # If models cannot be imported at module import time (e.g., during migrations), skip.
    models = None
