from __future__ import annotations
from typing import List, Tuple
from app.db.database import get_conn

def add_event(user_id: int, item_id: int, action: str) -> None:
    if action not in {"like", "dislike"}:
        raise ValueError("action must be like|dislike")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO events (user_id, item_id, action) VALUES (?, ?, ?)",
            (user_id, item_id, action),
        )
        conn.commit()

def get_user_feedback_item_ids(user_id: int) -> Tuple[List[int], List[int]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT item_id, action FROM events WHERE user_id = ?",
            (user_id,),
        )
        rows = cur.fetchall()

    liked_set = set()
    disliked_set = set()
    for item_id, action in rows:
        if action == "like":
            liked_set.add(int(item_id))
        elif action == "dislike":
            disliked_set.add(int(item_id))

    return sorted(liked_set), sorted(disliked_set)
