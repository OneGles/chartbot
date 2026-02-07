from __future__ import annotations
from typing import List
from app.core.llm_client import llm

def embed_texts(texts: List[str]) -> List[List[float]]:
    # llm.embed già ritorna list[list[float]]
    return llm.embed(texts)
