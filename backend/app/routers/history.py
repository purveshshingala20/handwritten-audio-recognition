"""History endpoint: lists all past recognitions stored locally."""
from flask import Blueprint, jsonify

from app import database

history_bp = Blueprint("history", __name__)


@history_bp.get("/api/history")
def get_history():
    rows = database.get_all_history()
    return jsonify(
        [
            {
                "id": row["id"],
                "filename": row["filename"],
                "recognized_text": row["recognized_text"],
                "confidence": row["confidence"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    )
