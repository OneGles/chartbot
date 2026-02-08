from __future__ import annotations
import json
import math
from typing import Any, Dict, List, Tuple

from app.db.database import get_conn
from app.retrieval.embeddings import embed_texts


def _cosine(a: List[float], b: List[float]) -> float:
    # defensive: dimensioni differenti => non corrisponde
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return -1.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def _fetch_domain_chunks(domain: str) -> List[Tuple[int, int, str, str]]:
    """
    Returns list of (chunk_id, item_id, title, embedding_json)
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT c.id, i.id, i.title, c.embedding
            FROM chunks c
            JOIN items i ON i.id = c.item_id
            WHERE i.domain = ?
            """,
            (domain,),
        )
        return cur.fetchall()


def _get_item_metadata(item_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT metadata_json, domain, title FROM items WHERE id = ?", (item_id,))
        row = cur.fetchone()
        if not row:
            return {}
        metadata_json, domain, title = row
        meta = json.loads(metadata_json) if metadata_json else {}
        meta["domain"] = domain
        meta["title"] = title
        meta["item_id"] = item_id
        return meta


def search(domain: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # 1) embed query
    q_emb = embed_texts([query])[0]

    # 2) fetch tutti gli embeddings dal dominio
    rows = _fetch_domain_chunks(domain)

    scored: List[Tuple[float, int]] = []
    for _chunk_id, item_id, _title, emb_json in rows:
        try:
            emb = json.loads(emb_json)
        except Exception:
            continue
        sim = _cosine(q_emb, emb)
        scored.append((sim, item_id))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: max(1, top_k)]

    # 3) Aggiorna metadata
    results: List[Dict[str, Any]] = []
    for sim, item_id in top:
        meta = _get_item_metadata(item_id)
        if not meta:
            continue
        meta["score"] = sim
        results.append(meta)

    return results
