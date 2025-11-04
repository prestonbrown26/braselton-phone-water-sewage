"""Database models for the Braselton AI Phone Agent."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine

from . import db


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover - sqlite specific
    """Ensure SQLite enforces foreign keys during local development."""
    
    # Only apply PRAGMA to SQLite connections, not PostgreSQL
    if dbapi_connection.__class__.__module__ == "sqlite3":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class CallLog(db.Model):  # type: ignore[misc]
    """Stores caller transcripts, metadata, and sentiment."""

    __tablename__ = "call_logs"

    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(64), unique=True, nullable=False)
    caller_number = db.Column(db.String(32))
    transcript = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float)
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "call_id": self.call_id,
            "caller_number": self.caller_number,
            "transcript": self.transcript,
            "sentiment_score": self.sentiment_score,
            "email_sent": self.email_sent,
            "created_at": self.created_at.isoformat(),
        }


