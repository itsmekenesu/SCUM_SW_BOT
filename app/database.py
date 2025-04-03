import sqlite3
import os

DATABASE_PATH = '/tmp/bots.db'

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS bots
                        (bot_id TEXT PRIMARY KEY,
                         last_seen TIMESTAMP,
                         callback_url TEXT,
                         public_ip TEXT,
                         version TEXT,
                         status TEXT)''')
        conn.commit()
    finally:
        conn.close()

def get_connection():
    return sqlite3.connect(DATABASE_PATH)
