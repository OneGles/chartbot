from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple

from app.db.database import get_conn
from .embeddings import embed_texts

BATCH_SIZE = 64

def build_chunk_text(domain: str, title: str, meta: Dict[str, Any]) -> str:
    text = meta.get("text", "")
    tags = meta.get("tags", [])
    people = meta.get("people", [])
    year = meta.get("year", None)

    parts = [
        f"domain: {domain}",
        f"title: {title}",
        f"text: {text}",
    ]
    if tags:
        parts.append("tags: " + ", ".join(tags))
    if people:
        parts.append("people: " + ", ".join(people))
    if year:
        parts.append(f"year: {year}")

    return "\n".join(parts).strip()


def fetch_items_missing_chunks() -> List[Tuple[int, str, str, Dict[str, Any]]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id, i.domain, i.title, i.metadata_json
            FROM items i
            LEFT JOIN chunks c ON c.item_id = i.id
            WHERE c.id IS NULL
            ORDER BY i.id
        """)
        rows = cur.fetchall()

    out = []
    for item_id, domain, title, metadata_json in rows:
        meta = json.loads(metadata_json) if metadata_json else {}
        out.append((item_id, domain, title, meta))
    return out


def insert_chunk(item_id: int, text: str, embedding: List[float]) -> None:
    emb_json = json.dumps(embedding)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chunks (item_id, text, embedding) VALUES (?, ?, ?)",
            (item_id, text, emb_json),
        )
        conn.commit()


def build_index() -> None:
    items = fetch_items_missing_chunks()
    if not items:
        print("No items to index (chunks already exist).")
        return

    batch_texts = []
    batch_ids = []

    for item_id, domain, title, meta in items:
        chunk_text = build_chunk_text(domain, title, meta)
        batch_texts.append(chunk_text)
        batch_ids.append(item_id)

        if len(batch_texts) >= BATCH_SIZE:
            _flush(batch_ids, batch_texts)
            batch_texts, batch_ids = [], []

    if batch_texts:
        _flush(batch_ids, batch_texts)

    print(f"Indexed {len(items)} items into chunks.")


def _flush(item_ids: List[int], texts: List[str]) -> None:
    embs = embed_texts(texts)
    with get_conn() as conn:
        cur = conn.cursor()
        for item_id, text, emb in zip(item_ids, texts, embs):
            cur.execute(
                "INSERT INTO chunks (item_id, text, embedding) VALUES (?, ?, ?)",
                (item_id, text, json.dumps(emb)),
            )
        conn.commit()
