from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("/app")  # nel container
DB_PATH = Path(os.getenv("DB_PATH", "data/app.db"))
SCHEMA_PATH = PROJECT_ROOT / "app" / "db" / "schema.sql"


def run_module(mod: str) -> None:
    print(f"== Run: python -m {mod}")
    subprocess.run([sys.executable, "-m", mod], check=True)


def ensure_dirs() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def exec_schema(conn: sqlite3.Connection) -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"schema.sql not found at {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)


def wipe_tables(conn: sqlite3.Connection) -> None:
    # ordine: chunks -> items (FK), events, users
    conn.execute("PRAGMA foreign_keys=OFF;")
    conn.execute("DELETE FROM chunks;")
    conn.execute("DELETE FROM items;")
    conn.execute("DELETE FROM events;")
    conn.execute("DELETE FROM users;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.commit()


def create_demo_user(conn: sqlite3.Connection, user_id: int = 1) -> None:
    conn.execute(
        "INSERT INTO users (id, profile_json, summary) VALUES (?, ?, ?)",
        (user_id, "{}", ""),
    )
    conn.commit()


def quick_verify(conn: sqlite3.Connection) -> None:
    print("== Verify: items per domain")
    for domain, cnt in conn.execute("SELECT domain, COUNT(*) FROM items GROUP BY domain ORDER BY domain;"):
        print(f"  {domain}: {cnt}")

    chunks_count = conn.execute("SELECT COUNT(*) FROM chunks;").fetchone()[0]
    users_count = conn.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
    events_count = conn.execute("SELECT COUNT(*) FROM events;").fetchone()[0]
    print(f"== Verify: chunks={chunks_count}, users={users_count}, events={events_count}")


def main() -> None:
    ensure_dirs()

    print("== Bootstrap: ensure schema ==")
    conn = sqlite3.connect(DB_PATH)
    try:
        exec_schema(conn)

        print("== Bootstrap: generate dataset (data/items.jsonl) ==")
        run_module("scripts.generate_items")

        print("== Bootstrap: wipe tables (items/chunks/events/users) ==")
        wipe_tables(conn)

        print("== Bootstrap: load items ==")
        run_module("scripts.load_items")

        print("== Bootstrap: build index (chunks + embeddings) ==")
        run_module("scripts.build_index")

        print("== Bootstrap: create demo user (id=1) ==")
        create_demo_user(conn, user_id=1)

        quick_verify(conn)
        print("== Bootstrap done ==")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
