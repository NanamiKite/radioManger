"""Isolated database fixtures; never open the application's configured database."""
import os

os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "regression-tests-only-secret-key-32-bytes"
os.environ["DATABASE_MODE"] = "sqlite"
os.environ["SQLITE_URL"] = "sqlite://"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
import app.models  # noqa: F401
from app.models.user import User
from app.utils.security import SecurityUtils


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, autoflush=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def users(db):
    password_hash = SecurityUtils.hash_password("password123")
    accounts = tuple(
        User(username=f"user_{suffix}", email=f"{suffix}@example.com", password_hash=password_hash,
             role="user", is_active=True, is_deleted=False)
        for suffix in ("a", "b")
    )
    db.add_all(accounts)
    db.commit()
    return accounts
