import requests
from .config import settings

class LLMClient:
    def chat(self, messages, temperature=0.3):
        resp = requests.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=30,
        )
        return resp.json()["choices"][0]["message"]["content"]

    def embed(self, texts):
        resp = requests.post(
            f"{settings.LLM_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.EMBED_MODEL,
                "input": texts,
            },
            timeout=30,
        )
        return [d["embedding"] for d in resp.json()["data"]]

llm = LLMClient()
