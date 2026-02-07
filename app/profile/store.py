import json
import sqlite3
from typing import Tuple, Optional

from app.db.database import get_conn
from .models import UserProfile


def get_user_profile_and_summary(user_id: int) -> Tuple[UserProfile, str]:
    """
    Returns (profile, summary). If user doesn't exist, creates empty.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT profile_json, summary FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()

        if row is None:
            profile = UserProfile()
            summary = ""
            cur.execute(
                "INSERT INTO users (id, profile_json, summary) VALUES (?, ?, ?)",
                (user_id, profile.model_dump_json(), summary),
            )
            conn.commit()
            return profile, summary

        profile_json, summary = row
        if profile_json:
            try:
                profile = UserProfile(**json.loads(profile_json))
            except Exception:
                profile = UserProfile()
        else:
            profile = UserProfile()

        return profile, (summary or "")


def save_user_profile_and_summary(user_id: int, profile: UserProfile, summary: str) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET profile_json = ?, summary = ? WHERE id = ?",
            (profile.model_dump_json(), summary, user_id),
        )
        conn.commit()
