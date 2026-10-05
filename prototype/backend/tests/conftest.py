"""Shared pytest fixtures.

Uses SQLite in-memory by default. If TEST_DATABASE_URL points at a Postgres DB,
tests run against that instead (schema.sql must already be applied there).
Note: the EXCLUDE USING gist (no-double-booking) constraint cannot be verified
on sqlite; tests that rely on it are skipped unless Postgres is used.
"""
from __future__ import annotations

import os
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
IS_POSTGRES = TEST_DB_URL.startswith("postgres")


@pytest.fixture()
def app_client():
    # Force the app's engine to use the test DB BEFORE importing the app.
    os.environ["DATABASE_URL"] = TEST_DB_URL
    os.environ["JWT_SECRET"] = "test-secret"

    # Reset cached settings so new DATABASE_URL takes effect.
    from app import config as _config
    _config.get_settings.cache_clear()

    from app import db as _db
    kwargs = {"future": True}
    if TEST_DB_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool  # share one in-memory DB across sessions
    engine = create_engine(TEST_DB_URL, **kwargs)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    _db.engine = engine
    _db.SessionLocal = TestingSession

    from app.db import Base
    from app import models  # noqa: F401 ensure tables registered
    from app.admin import service as _admin_service  # noqa: F401 registers AuditEntry on Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    _seed(TestingSession)

    from app.main import app
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


def _seed(SessionLocal) -> None:
    """Insert two locations, two vehicle categories, two vehicles."""
    from app.models import Location, VehicleCategory, Vehicle
    with SessionLocal() as s:
        loc1 = Location(code="JFK", name="JFK Airport", address="JFK", opens_at=time(6, 0), closes_at=time(23, 0))
        loc2 = Location(code="LGA", name="LGA Airport", address="LGA", opens_at=time(6, 0), closes_at=time(23, 0))
        s.add_all([loc1, loc2])
        s.flush()

        cat_sedan = VehicleCategory(name="Sedan", daily_rate=50, flat_fee=25)
        cat_suv = VehicleCategory(name="SUV", daily_rate=80, flat_fee=40)
        s.add_all([cat_sedan, cat_suv])
        s.flush()

        v1 = Vehicle(vin="VIN111", make="Toyota", model="Camry", year=2022, seats=5, status="AVAILABLE",
                     category_id=cat_sedan.id, home_location_id=loc1.id)
        v2 = Vehicle(vin="VIN222", make="Honda", model="CR-V", year=2023, seats=5, status="AVAILABLE",
                     category_id=cat_suv.id, home_location_id=loc1.id)
        s.add_all([v1, v2])
        s.commit()


def make_admin(client, email="admin@example.com", password="correcthorse"):
    """Create an ADMIN user directly via the SessionLocal, then login to get a token.

    Added additively for admin tests; does not modify existing fixtures.
    """
    from app import db as _db
    from app.models import User
    from app.security import hash_password, create_access_token

    with _db.SessionLocal() as s:
        existing = s.query(User).filter(User.email == email).first()
        if existing is None:
            u = User(email=email, password_hash=hash_password(password), role="ADMIN", staff_id="S-1")
            s.add(u)
            s.commit()
            s.refresh(u)
            uid = u.id
        else:
            uid = existing.id
    token = create_access_token(subject=uid, role="ADMIN")
    return {"user_id": uid, "token": token, "email": email}


def register_payload(email="alice@example.com", age=30, licence_days=365):
    today = date.today()
    dob = date(today.year - age, today.month, today.day)
    exp = date(today.year + (licence_days // 365 or 1), today.month, today.day)
    return {
        "email": email,
        "password": "correcthorse",
        "first_name": "Alice",
        "last_name": "A",
        "date_of_birth": dob.isoformat(),
        "phone": "555-1234",
        "licence": {"number": "DL123", "issuing_state": "NY", "expires_on": exp.isoformat()},
    }
