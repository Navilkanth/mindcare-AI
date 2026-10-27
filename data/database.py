"""
MindCare AI — Database Layer
Sets up SQLite tables for sessions, messages, and mood logs.
"""
import sqlite3
import os
from config import settings


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory and WAL mode for high concurrency."""
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,          -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # Mood logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            mood_score INTEGER NOT NULL,  -- 1-10 user self-reported score
            primary_emotion TEXT,
            ai_intensity INTEGER,
            key_themes TEXT,              -- JSON string
            note TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── Session Helpers ──────────────────────────────────────────────────────────

def create_session(session_id: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id) VALUES (?)", (session_id,)
    )
    conn.commit()
    conn.close()


def update_session_activity(session_id: str) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE sessions
           SET last_active = CURRENT_TIMESTAMP,
               message_count = message_count + 1
           WHERE id = ?""",
        (session_id,),
    )
    conn.commit()
    conn.close()


# ─── Message Helpers ──────────────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    conn.commit()
    conn.close()


def get_messages(session_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Mood Log Helpers ─────────────────────────────────────────────────────────

def save_mood_log(
    session_id: str,
    mood_score: int,
    primary_emotion: str = None,
    ai_intensity: int = None,
    key_themes: list = None,
    note: str = None,
) -> None:
    import json
    conn = get_connection()
    conn.execute(
        """INSERT INTO mood_logs
           (session_id, mood_score, primary_emotion, ai_intensity, key_themes, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            mood_score,
            primary_emotion,
            ai_intensity,
            json.dumps(key_themes or []),
            note,
        ),
    )
    conn.commit()
    conn.close()


def get_mood_logs(session_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM mood_logs WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
