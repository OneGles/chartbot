from __future__ import annotations
import json
from typing import Any, Dict

from app.core.llm_client import llm
from app.profile.models import UserProfile

SYSTEM_PROMPT = """You generate a grounded recommendation response for an arts recommender.

Return ONLY valid JSON.

Hard rules:
- Use ONLY the provided candidate items. Do NOT mention any other titles/artists.
- Keep it concise and in Italian.
- For each domain (film, book, music, game), provide:
  - title
  - one short reason (1-2 sentences) grounded in the item's snippet/tags/people
  - "because" bullets: 2-3 bullet reasons tied to the user's profile summary/constraints
- Respect constraints (e.g., no gore, avoid jumpscares).
- Do not invent details not present in the item data.
- Do NOT claim an item has/has-not gore/jumpscares unless the bundle text/tags explicitly mention it. Prefer phrasing like "in linea con la tua preferenza no gore".

JSON schema:
{
  "message": "string",
  "by_domain": {
    "film": {"title": "string", "reason": "string", "because": ["string"]},
    "book": {"title": "string", "reason": "string", "because": ["string"]},
    "music": {"title": "string", "reason": "string", "because": ["string"]},
    "game": {"title": "string", "reason": "string", "because": ["string"]}
  }
}
"""

def explain(profile_summary: str, constraints: list[str], bundle: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "profile_summary": profile_summary,
        "constraints": constraints,
        "bundle": {
            d: {
                "title": (bundle.get(d) or {}).get("title"),
                "text": (bundle.get(d) or {}).get("text"),
                "tags": (bundle.get(d) or {}).get("tags"),
                "people": (bundle.get(d) or {}).get("people"),
                "year": (bundle.get(d) or {}).get("year"),
                "p": (bundle.get(d) or {}).get("p"),
            }
            for d in ["film", "book", "music", "game"]
        },
    }

    raw = llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(raw)
    except Exception:
        # fallback minimale: niente LLM
        return {
            "message": "Ecco alcuni consigli coerenti con le tue preferenze.",
            "by_domain": {
                d: {"title": (bundle.get(d) or {}).get("title"), "reason": "", "because": []}
                for d in ["film", "book", "music", "game"]
            },
        }
