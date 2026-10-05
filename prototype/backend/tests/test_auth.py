"""Auth tests. F.R 1.1, 1.2."""
from __future__ import annotations

from datetime import date, timedelta

from .conftest import register_payload


def test_register_rejects_under_21(app_client):
    body = register_payload(email="young@example.com", age=19)
    r = app_client.post("/auth/register", json=body)
    assert r.status_code == 400
    assert "21" in r.json()["detail"]


def test_register_rejects_expired_licence(app_client):
    body = register_payload(email="exp@example.com", age=30)
    body["licence"]["expires_on"] = (date.today() - timedelta(days=1)).isoformat()
    r = app_client.post("/auth/register", json=body)
    assert r.status_code == 400
    assert "licence" in r.json()["detail"].lower()


def test_register_and_login_happy_path(app_client):
    body = register_payload(email="alice@example.com", age=30)
    r = app_client.post("/auth/register", json=body)
    assert r.status_code == 201, r.text
    token = r.json()
    assert token["access_token"]
    assert token["role"] == "CUSTOMER"

    r2 = app_client.post("/auth/login", json={"email": body["email"], "password": body["password"]})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_login_rejects_bad_password(app_client):
    body = register_payload(email="alice@example.com", age=30)
    app_client.post("/auth/register", json=body)
    r = app_client.post("/auth/login", json={"email": body["email"], "password": "wrong"})
    assert r.status_code == 401
