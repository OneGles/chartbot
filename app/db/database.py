import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "data/app.db")

def get_conn():
    return sqlite3.connect(DB_PATH)
