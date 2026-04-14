import os
import httpx
from typing import Optional
import asyncio

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

    async def chat_stream(self, model: str, prompt: str):
        """Async generator that yields text chunks from the model.

        Attempts to connect to Ollama's standard completion endpoint with streaming.
        If streaming isn't supported, falls back to returning the full completion
        in a few artificial chunks to allow the frontend to render progressively.
        """
        url = f"{self.base_url}/v1/engines/{model}/completions"
        payload = {"prompt": prompt, "max_tokens": 512, "temperature": 0.2}

        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", url, json=payload) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_text(chunk_size=512):
                        if not chunk:
                            continue
                        # Yield raw text chunks as they arrive
                        yield chunk
                    return
            except Exception:
                # Fallback: synchronous call and chunk the reply
                try:
                    loop = asyncio.get_event_loop()
                    resp = await loop.run_in_executor(None, self.chat, model, prompt)
                    # extract text
                    reply_text = None
                    if isinstance(resp, dict):
                        if "text" in resp:
                            reply_text = resp["text"]
                        elif "choices" in resp and len(resp["choices"]) > 0:
                            reply_text = resp["choices"][0].get("text") or resp["choices"][0].get("message", {}).get("content")
                    if reply_text is None:
                        reply_text = str(resp)

                    # yield in modest-sized chunks
                    chunk_size = 120
                    for i in range(0, len(reply_text), chunk_size):
                        await asyncio.sleep(0)  # allow event loop to breathe
                        yield reply_text[i:i+chunk_size]
                except Exception:
                    # final fallback: single short message
                    yield "[error retrieving stream]"

# Example usage:
# client = OllamaClient()
# r = client.chat('local-instruct', 'Say hello')
# print(r)
