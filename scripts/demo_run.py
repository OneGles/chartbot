from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

DB_PATH = Path(os.getenv("DB_PATH", "data/app.db"))
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

DOMAINS = ["film", "book", "music", "game"]


def post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def reset_demo_user(user_id: int = 1) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM events WHERE user_id=?;", (user_id,))
        conn.execute("UPDATE users SET profile_json='{}', summary='' WHERE id=?;", (user_id,))
        conn.commit()
    finally:
        conn.close()


def _pick(item: Dict[str, Any]) -> Tuple[int, str, int | None, float | None, float | None]:
    # (item_id, title, year, score, p)
    return (
        int(item.get("item_id")),
        str(item.get("title")),
        int(item["year"]) if item.get("year") is not None else None,
        float(item["score"]) if item.get("score") is not None else None,
        float(item["p"]) if item.get("p") is not None else None,
    )


def print_bundle(label: str, bundle: Dict[str, Any]) -> Dict[str, Tuple[int, str, int | None, float | None, float | None]]:
    print()
    print(f"=== {label} ===")
    out: Dict[str, Tuple[int, str, int | None, float | None, float | None]] = {}

    for d in DOMAINS:
        it = bundle.get(d)
        if not it:
            print(f"- {d:5} : (none)")
            continue

        item_id, title, year, score, p = _pick(it)
        out[d] = (item_id, title, year, score, p)

        year_s = f"{year}" if year is not None else "?"
        score_s = f"{score:.4f}" if score is not None else "?"
        p_s = f"{p:.3f}" if p is not None else "?"
        print(f"- {d:5} : {title} ({year_s})  id={item_id}  score={score_s}  p={p_s}")

    return out


def print_delta(before: Dict[str, Tuple[int, str, int | None, float | None, float | None]],
                after: Dict[str, Tuple[int, str, int | None, float | None, float | None]]) -> None:
    print()
    print("=== Delta (after - before) ===")
    for d in DOMAINS:
        if d not in before or d not in after:
            continue
        b = before[d]
        a = after[d]
        b_score = b[3]
        a_score = a[3]
        if b_score is None or a_score is None:
            continue
        ds = a_score - b_score
        changed = "CHANGED" if a[0] != b[0] else "same"
        print(f"- {d:5} : score Δ={ds:+.4f}   item {changed}")


def main() -> None:
    print("== Demo: reset user 1 + events ==")
    reset_demo_user(user_id=1)

    print("== Demo: seed preferences via /chat (3 messages) ==")

    r_chat1 = post_json(
        "/chat",
        {"user_id": 1, "message": "Mi piacciono i thriller psicologici tipo Shutter Island. Niente gore."},
    )
    r_chat2 = post_json(
        "/chat",
        {"user_id": 1, "message": "In musica: dark ambient e colonne sonore tese, atmosfera cupa."},
    )
    r_chat3 = post_json(
        "/chat",
        {"user_id": 1, "message": "Nei videogiochi: horror narrativo e psicologico. No jumpscare continui."},
    )

    summary = r_chat3.get("summary", "")
    print()
    print("=== User summary after chat ===")
    print(summary)


    r1 = post_json("/recommend", {"user_id": 1, "top_k_per_domain": 8})
    bundle1 = r1["recommendations"]["bundle"]
    b1 = print_bundle("Baseline recommendations", bundle1)

    music_id = bundle1["music"]["item_id"]
    film_id = bundle1["film"]["item_id"]

    print()
    print(f"== Feedback: LIKE music item_id={music_id} ==")
    post_json("/feedback", {"user_id": 1, "item_id": music_id, "action": "like"})

    r2 = post_json("/recommend", {"user_id": 1, "top_k_per_domain": 8})
    bundle2 = r2["recommendations"]["bundle"]
    b2 = print_bundle("After LIKE (music)", bundle2)
    print_delta(b1, b2)

    print()
    print(f"== Feedback: DISLIKE film item_id={film_id} ==")
    post_json("/feedback", {"user_id": 1, "item_id": film_id, "action": "dislike"})

    r3 = post_json("/recommend", {"user_id": 1, "top_k_per_domain": 8})
    bundle3 = r3["recommendations"]["bundle"]
    b3 = print_bundle("After DISLIKE (film)", bundle3)
    print_delta(b2, b3)

    print()
    print("== Demo done ==")


if __name__ == "__main__":
    main()
