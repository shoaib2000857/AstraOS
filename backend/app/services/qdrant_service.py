import os

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except ImportError:  # pragma: no cover - optional dependency
    QdrantClient = None
    qmodels = None

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_TIMEOUT_SECONDS = float(os.getenv("QDRANT_TIMEOUT_SECONDS", "2"))

_client = None


def is_available() -> bool:
    return QdrantClient is not None


def get_client():
    global _client
    if not is_available():
        raise RuntimeError("qdrant-client is not installed")
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT_SECONDS)
    return _client


def ensure_collection(name: str, vector_size: int):
    client = get_client()
    try:
        client.get_collection(name=name)
    except Exception:
        client.recreate_collection(collection_name=name, vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE))


def upsert_vectors(collection: str, vectors: list[tuple]):
    # vectors: list of (id, vector, payload dict)
    client = get_client()
    points = [qmodels.PointStruct(id=vid, vector=vec, payload=payload) for (vid, vec, payload) in vectors]
    client.upsert(collection_name=collection, points=points)


def search(collection: str, query_vector, top_k: int = 5, filter=None):
    client = get_client()
    hits = client.search(collection_name=collection, query_vector=query_vector, limit=top_k, filter=filter)
    return hits
