import os
import httpx
from typing import Optional

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or OLLAMA_URL
        self._client = httpx.Client(timeout=30)

    def chat(self, model: str, prompt: str):
        """Simple sync call to Ollama's chat endpoint (assumes OpenAI-compatible API).
        This is a minimal placeholder — adapt to your Ollama deployment API."""
        url = f"{self.base_url}/v1/engines/{model}/completions"
        payload = {
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.2,
        }
        resp = self._client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def embed_text(self, model: str, texts: list[str]):
        """Request embeddings for a list of texts.
        Tries Ollama/OpenAI-compatible `/v1/embeddings` first; falls back to a zero-vector placeholder.
        """
        url = f"{self.base_url}/v1/embeddings"
        payload = {"model": model, "input": texts}
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Expecting {'data': [{'embedding': [...]}, ...]} or OpenAI-style response
            if isinstance(data, dict) and "data" in data:
                embeddings = []
                for item in data["data"]:
                    emb = item.get("embedding") or item.get("vector")
                    embeddings.append(emb)
                return embeddings
            return []
        except Exception:
            # Return placeholder zero vectors sized 768 by default
            return [[0.0] * 768 for _ in texts]

# Example usage:
# client = OllamaClient()
# r = client.chat('local-instruct', 'Say hello')
# print(r)
