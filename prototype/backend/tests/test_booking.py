"""Booking tests. F.R 3.x / 4.x."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from .conftest import register_payload, IS_POSTGRES


def _register_and_login(client, email="alice@example.com"):
    body = register_payload(email=email, age=30)
    r = client.post("/auth/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _first_vehicle(client):
    r = client.get("/vehicles")
    assert r.status_code == 200
    assert r.json(), "seeded vehicles missing"
    return r.json()[0]


def _window():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    end = start + timedelta(days=3)
    return start.isoformat(), end.isoformat()


def test_quote_reserve_pay_confirmed(app_client):
    token = _register_and_login(app_client)
    v = _first_vehicle(app_client)
    start, end = _window()

    q = app_client.post("/bookings/quote", json={
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
    }, headers=_auth(token))
    assert q.status_code == 200
    quote = q.json()
    assert quote["days"] == 3
    # daily_rate(50) * 3 + flat_fee(25) = 175
    assert float(quote["subtotal"]) == 175.0
    assert float(quote["total"]) == 175.0

    r = app_client.post("/bookings", json={
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }, headers=_auth(token))
    assert r.status_code == 201, r.text
    booking = r.json()
    assert booking["status"] == "INPROGRESS"
    assert float(booking["quote_total"]) == 175.0

    p = app_client.post(f"/bookings/{booking['id']}/pay", json={
        "card_number": "4242424242424242", "exp_month": 12, "exp_year": 2030, "cvc": "123",
        "idempotency_key": "idem-ok-1",
    }, headers=_auth(token))
    assert p.status_code == 200, p.text
    assert p.json()["status"] == "CONFIRMED"


def test_mock_declined_card_sets_failed_payment_and_hold(app_client):
    """F.R 4.4 — on failed payment, status=FAILED_PAYMENT with hold_expires_at set."""
    token = _register_and_login(app_client)
    v = _first_vehicle(app_client)
    start, end = _window()

    r = app_client.post("/bookings", json={
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }, headers=_auth(token))
    booking_id = r.json()["id"]

    p = app_client.post(f"/bookings/{booking_id}/pay", json={
        "card_number": "4000000000000002", "exp_month": 12, "exp_year": 2030, "cvc": "123",
        "idempotency_key": "idem-fail-1",
    }, headers=_auth(token))
    assert p.status_code == 402
    detail = p.json()["detail"]
    assert detail["booking_status"] == "FAILED_PAYMENT"
    assert detail["hold_expires_at"]  # populated


@pytest.mark.skipif(
    not IS_POSTGRES,
    reason="EXCLUDE USING gist is a Postgres-only constraint; cannot be exercised on sqlite. "
           "Set TEST_DATABASE_URL=postgresql+psycopg2://... (with schema.sql applied) to run.",
)
def test_double_book_returns_409(app_client):
    """F.R 3.3 / 2.4 — Postgres EXCLUDE constraint translated to HTTP 409."""
    token = _register_and_login(app_client)
    v = _first_vehicle(app_client)
    start, end = _window()

    body = {
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }
    r1 = app_client.post("/bookings", json=body, headers=_auth(token))
    assert r1.status_code == 201

    token2 = _register_and_login(app_client, email="bob@example.com")
    r2 = app_client.post("/bookings", json=body, headers=_auth(token2))
    assert r2.status_code == 409
    assert "already booked" in r2.json()["detail"]


@pytest.mark.skipif(not IS_POSTGRES, reason="needs Postgres EXCLUDE constraint")
def test_exclude_constraint_alone_returns_409(app_client, monkeypatch):
    """Bypass the app-level guard so ONLY the DB EXCLUDE (SQLSTATE 23P01) stops the double booking."""
    from app.booking import service
    monkeypatch.setattr(service, "LIVE_STATUSES", ("EXPIRED",))  # guard now matches nothing
    token = _register_and_login(app_client)
    token2 = _register_and_login(app_client, email="bob@example.com")
    v = _first_vehicle(app_client)
    start, end = _window()
    body = {
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }
    assert app_client.post("/bookings", json=body, headers=_auth(token)).status_code == 201
    r2 = app_client.post("/bookings", json=body, headers=_auth(token2))
    assert r2.status_code == 409, r2.text
    assert "already booked" in r2.json()["detail"]


def test_app_level_overlap_guard_also_returns_409(app_client):
    """Even on sqlite the app-level overlap check should prevent duplicates."""
    token = _register_and_login(app_client)
    v = _first_vehicle(app_client)
    start, end = _window()

    body = {
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }
    r1 = app_client.post("/bookings", json=body, headers=_auth(token))
    assert r1.status_code == 201
    r2 = app_client.post("/bookings", json=body, headers=_auth(token))
    assert r2.status_code == 409


def test_cancel_before_pickup(app_client):
    token = _register_and_login(app_client)
    v = _first_vehicle(app_client)
    start, end = _window()
    r = app_client.post("/bookings", json={
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }, headers=_auth(token))
    bid = r.json()["id"]
    c = app_client.post(f"/bookings/{bid}/cancel", headers=_auth(token))
    assert c.status_code == 200
    assert c.json()["status"] == "CANCELLED"


def test_list_mine_scoped_to_user(app_client):
    token_a = _register_and_login(app_client, "a@example.com")
    token_b = _register_and_login(app_client, "b@example.com")
    v = _first_vehicle(app_client)
    start, end = _window()
    app_client.post("/bookings", json={
        "vehicle_id": v["id"], "period_start": start, "period_end": end,
        "pickup_location_id": v["home_location_id"], "return_location_id": v["home_location_id"],
    }, headers=_auth(token_a))
    rb = app_client.get("/bookings", headers=_auth(token_b))
    assert rb.status_code == 200
    assert rb.json() == []
