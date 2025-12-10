#!/usr/bin/env python3
"""Initialize database tables and seed an initial admin user if missing."""

import os

from app import app, db
from app.models import User

if __name__ == "__main__":
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        if User.query.count() == 0:
            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD", "changeme")
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"✓ Seeded initial admin user '{username}' (change this password immediately).")
        else:
            print("✓ Users already exist; skipping seed.")
        print("✓ Database tables created successfully!")

