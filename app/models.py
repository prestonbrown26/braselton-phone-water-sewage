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
    """Stores caller transcripts, metadata, and sentiment.
    
    Per Georgia state law LG 20-022:
    - Utility account communication: 5-year retention
    - Dispute-related: Keep until resolved + 5 years
    - Emergency-related: 5 years after resolution
    
    Solution: Store ALL transcripts for 5 years (simplest approach per Blake's request)
    """

    __tablename__ = "call_logs"

    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    caller_number = db.Column(db.String(32), index=True)
    transcript = db.Column(db.Text, nullable=False)
    duration_seconds = db.Column(db.Integer)
    sentiment = db.Column(db.String(20))  # positive, neutral, negative
    transferred = db.Column(db.Boolean, default=False, nullable=False)
    email_sent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "call_id": self.call_id,
            "caller_number": self.caller_number,
            "transcript": self.transcript,
            "duration_seconds": self.duration_seconds,
            "sentiment": self.sentiment,
            "transferred": self.transferred,
            "email_sent": self.email_sent,
            "created_at": self.created_at.isoformat(),
        }


