import sqlite3
import os

DB_PATH = "proxies.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rekeys (
            rk_id TEXT PRIMARY KEY,
            from_user TEXT,
            to_user TEXT,
            blob TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
