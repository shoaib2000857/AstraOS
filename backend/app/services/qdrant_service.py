import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")

_client: QdrantClient | None = None


def get_client():
    global _client
    if _client is None:
        # QdrantClient accepts host and prefer_grpc options; using http endpoint here
        _client = QdrantClient(url=QDRANT_URL)
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
