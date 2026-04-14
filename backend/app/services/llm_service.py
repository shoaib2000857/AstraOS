import asyncio
import json
import os
from typing import Optional

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
DEFAULT_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def chunk_text(text: str, chunk_size: int = 140):
    for index in range(0, len(text), chunk_size):
        yield text[index:index + chunk_size]


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or OLLAMA_URL
        self._client = httpx.Client(timeout=httpx.Timeout(30.0, connect=2.0))

    @staticmethod
    def extract_text(payload):
        if isinstance(payload, dict):
            if "choices" in payload and payload["choices"]:
                choice = payload["choices"][0]
                message = choice.get("message") or {}
                delta = choice.get("delta") or {}
                return message.get("content") or delta.get("content") or choice.get("text")
            if "message" in payload and isinstance(payload["message"], dict):
                return payload["message"].get("content")
            if "response" in payload:
                return payload["response"]
            if "text" in payload:
                return payload["text"]
        if isinstance(payload, str):
            return payload
        return None

    def _chat_v1(self, model: str, messages: list[dict], temperature: float = 0.2, max_tokens: int = 512):
        response = self._client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()

    def _chat_native(self, model: str, messages: list[dict], temperature: float = 0.2, max_tokens: int = 512):
        response = self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        return response.json()

    def chat(self, model: Optional[str], prompt: str):
        return self.chat_messages(model=model, messages=[{"role": "user", "content": prompt}])

    def chat_messages(
        self,
        model: Optional[str],
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        selected_model = model or DEFAULT_CHAT_MODEL
        try:
            return self._chat_v1(selected_model, messages, temperature=temperature, max_tokens=max_tokens)
        except Exception:
            return self._chat_native(selected_model, messages, temperature=temperature, max_tokens=max_tokens)

    def embed_text(self, model: Optional[str], texts: list[str]):
        selected_model = model or DEFAULT_EMBEDDING_MODEL
        try:
            response = self._client.post(
                f"{self.base_url}/v1/embeddings",
                json={"model": selected_model, "input": texts},
                timeout=httpx.Timeout(8.0, connect=2.0),
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return [(item.get("embedding") or item.get("vector")) for item in data["data"]]
        except Exception:
            pass

        for path in ("/api/embed", "/api/embeddings"):
            try:
                response = self._client.post(
                    f"{self.base_url}{path}",
                    json={"model": selected_model, "input": texts},
                    timeout=httpx.Timeout(8.0, connect=2.0),
                )
                response.raise_for_status()
                data = response.json()
                if "embeddings" in data:
                    return data["embeddings"]
                if "embedding" in data:
                    return [data["embedding"]]
            except Exception:
                continue
        return []

    async def chat_stream_messages(
        self,
        model: Optional[str],
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        selected_model = model or DEFAULT_CHAT_MODEL
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": selected_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    buffer = ""
                    async for raw in response.aiter_text():
                        if not raw:
                            continue
                        buffer += raw
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data = line[5:].strip()
                            if data == "[DONE]":
                                return
                            parsed = json.loads(data)
                            text = self.extract_text(parsed)
                            if text:
                                yield text
                    return
            except Exception:
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        self.chat_messages,
                        selected_model,
                        messages,
                        temperature,
                        max_tokens,
                    )
                    reply_text = self.extract_text(response) or str(response)
                    for piece in chunk_text(reply_text):
                        await asyncio.sleep(0)
                        yield piece
                except Exception:
                    yield "[error retrieving stream]"

    async def chat_stream(self, model: Optional[str], prompt: str):
        async for piece in self.chat_stream_messages(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        ):
            yield piece
