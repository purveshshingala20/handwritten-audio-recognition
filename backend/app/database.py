"""Lightweight SQLite persistence for recognition history."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, List, Optional

from app.config import DB_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recognitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                model_used TEXT NOT NULL,
                recognized_text TEXT,
                confidence REAL,
                timestamp TEXT NOT NULL
            )
            """
        )


def insert_recognition(
    filename: str,
    file_size: int,
    file_type: str,
    model_used: str,
    recognized_text: str,
    confidence: float,
) -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO recognitions
                (filename, file_size, file_type, model_used, recognized_text, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (filename, file_size, file_type, model_used, recognized_text, confidence, timestamp),
        )
        row_id = cursor.lastrowid
    return {
        "id": row_id,
        "filename": filename,
        "file_size": file_size,
        "file_type": file_type,
        "model_used": model_used,
        "recognized_text": recognized_text,
        "confidence": confidence,
        "timestamp": timestamp,
    }


def get_all_history(limit: Optional[int] = None) -> List[dict]:
    query = "SELECT * FROM recognitions ORDER BY id DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
