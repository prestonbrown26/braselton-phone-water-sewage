#!/usr/bin/env python3
"""Initialize database tables for production deployment."""

from app import app, db

if __name__ == "__main__":
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")

