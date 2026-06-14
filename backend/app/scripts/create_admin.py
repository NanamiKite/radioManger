"""
管理员账户创建脚本
用法: python -m app.scripts.create_admin [username] [password] [email]
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.database.base import Base, engine, SessionLocal
from app.models import User  # noqa: ensure model registered
from app.utils.security import SecurityUtils


def create_admin(
    username: str = "admin",
    password: str = "admin123",
    email: str = "admin@radiomanager.dev",
):
    """创建管理员账户（自动创建表）"""
    # 确保表已创建
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
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
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        return admin
    finally:
        db.close()


if __name__ == "__main__":
    username = os.getenv("ADMIN_USERNAME", sys.argv[1] if len(sys.argv) > 1 else "admin")
    password = os.getenv("ADMIN_PASSWORD", sys.argv[2] if len(sys.argv) > 2 else "admin123")
    email = os.getenv("ADMIN_EMAIL", sys.argv[3] if len(sys.argv) > 3 else "admin@radiomanager.local")
    create_admin(username, password, email)
