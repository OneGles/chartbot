import requests
from app.core.config import settings

class LLMClient:
    def chat(self, messages, temperature=0.3, response_format=None):
        url = f"{settings.LLM_BASE_URL}/chat/completions"
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        # Per estrazione JSON: response_format={"type":"json_object"}
        if response_format is not None:
            payload["response_format"] = response_format

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        # Se OpenAI risponde con errore, il body contiene "error" 
        if resp.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if "choices" not in data or not data["choices"]:
            raise RuntimeError(f"LLM unexpected response: {data}")

        return data["choices"][0]["message"]["content"]

    def embed(self, texts):
        url = f"{settings.LLM_BASE_URL}/embeddings"
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": settings.EMBED_MODEL, "input": texts},
            timeout=60,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"EMBED HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if "data" not in data:
            raise RuntimeError(f"Embedding unexpected response: {data}")

        return [d["embedding"] for d in data["data"]]

llm = LLMClient()
