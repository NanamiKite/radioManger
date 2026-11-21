"""Explicit loopback MySQL opt-in; create/drop only a UUID-named test database."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.scripts.init_db import init_database


@pytest.fixture
def api_mode():
    return "mysql"


@pytest.fixture
def db():
    value = os.environ.get("RADIO_TEST_MYSQL_ADMIN_URL")
    if not value:
        pytest.fail("Real MySQL tests require RADIO_TEST_MYSQL_ADMIN_URL for a disposable loopback server; no production database is accepted.")
    url = make_url(value)
    if url.drivername != "mysql+pymysql" or url.host not in ("127.0.0.1", "localhost") or url.database:
        pytest.fail("Use a mysql+pymysql loopback admin URL with no database; tests create their own UUID database.")
    name = "radio_contract_" + uuid4().hex
    admin = create_engine(url, pool_pre_ping=True)
    engine = None
    try:
        with admin.begin() as connection:
            connection.exec_driver_sql(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        engine = create_engine(url.set(database=name), pool_pre_ping=True, pool_recycle=3600)
        init_database(database_engine=engine)
        with sessionmaker(bind=engine, autoflush=False)() as session:
            yield session
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{name}`")
        admin.dispose()
