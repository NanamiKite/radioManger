"""
管理员账户创建脚本
用法: ADMIN_PASSWORD=... python -m app.scripts.create_admin [username] [email]
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.database.base import SessionLocal
from app.models import User  # noqa: ensure model registered
from app.utils.security import SecurityUtils


def create_admin(
    username: str,
    password: str,
    email: str = "admin@radiomanager.local",
):
    """Create an explicitly requested administrator in a migrated database."""
    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        raise ValueError("Password must contain at least 8 characters and at most 72 UTF-8 bytes")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            if existing.role != "admin":
                raise ValueError(f"Username '{username}' belongs to a non-admin account")
            print(f"ℹ️  Admin user '{username}' already exists.")
            return existing

        admin = User(
            username=username,
            email=email,
            password_hash=SecurityUtils.hash_password(password),
            role="admin",
            is_active=True,
            full_name="System Admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        return admin
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    username = os.getenv("ADMIN_USERNAME", sys.argv[1] if len(sys.argv) > 1 else "admin")
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        from getpass import getpass
        password = getpass("Administrator password: ")
    email = os.getenv("ADMIN_EMAIL", sys.argv[2] if len(sys.argv) > 2 else "admin@radiomanager.local")
    create_admin(username, password, email)
