from __future__ import annotations
import json
from typing import Any, Dict

from app.core.llm_client import llm
from .models import UserUpdate


SYSTEM_PROMPT = """You extract structured user preferences for an arts recommender chatbot.

Return ONLY valid JSON and nothing else.

Allowed domains: film, book, music, game.

Schema:
{
  "likes": [string],
  "dislikes": [string],
  "likes_by_domain": { "film": [string], "book": [string], "music": [string], "game": [string] },
  "dislikes_by_domain": { "film": [string], "book": [string], "music": [string], "game": [string] },
  "seeds": [string],
  "constraints": [string],
  "mood": [string]
}

Hard rules:
- Put TITLES (movies, books, albums, games) ONLY in "seeds".
- Put PEOPLE names (director/author/artist/studio) in likes_by_domain for the relevant domain OR in "likes" if generic.
- likes_by_domain/dislikes_by_domain MUST contain preference tags (genres, styles, mechanics, themes), not titles.
- "constraints" contains negations like "no gore", "only Italian", "short games".
- Do NOT duplicate: if something is a seed title, do not repeat it in likes_by_domain.
- If uncertain, leave fields empty.
"""


def _safe_json_loads(s: str) -> Dict[str, Any]:
    """
    Best-effort parse: tries to locate the first JSON object in the string.
    """
    s = s.strip()
    # If model returns extra text, try to slice to the outermost braces
    if not s.startswith("{"):
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            s = s[start : end + 1]
    try:
        return json.loads(s)
    except Exception:
        return {}


def extract_update(user_message: str, profile_summary: str) -> UserUpdate:
    user_payload = {
        "message": user_message,
        "known_profile_summary": profile_summary[:1500],  # keep bounded
    }

    raw = llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    data = _safe_json_loads(raw)
    return UserUpdate(**data)
