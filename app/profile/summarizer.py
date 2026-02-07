from __future__ import annotations
import json

from app.core.llm_client import llm
from .models import UserProfile


SYSTEM_PROMPT = """You maintain a short, practical user memory for an arts recommender chatbot.

Return ONLY plain text (no JSON).
Write in Italian.
Keep it short (max ~1200 characters).
Focus on stable preferences, dislikes, constraints, mood, and a few seeds.
Do NOT add new facts not supported by inputs.
"""


def update_summary(old_summary: str, new_message: str, profile: UserProfile) -> str:
    payload = {
        "old_summary": old_summary,
        "new_message": new_message,
        "current_profile": profile.model_dump(),
    }

    text = llm.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0.2,
    ).strip()

    # Hard clamp (defensive)
    if len(text) > 1200:
        text = text[:1200].rsplit(" ", 1)[0]
    return text
