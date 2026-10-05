"""Admin endpoint tests. F.R 5.1-5.5 / UC-19..UC-23 / F.R 1.4."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .conftest import make_admin, register_payload


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register_customer(client, email="cust@example.com"):
    r = client.post("/auth/register", json=register_payload(email=email, age=30))
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _window():
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    end = start + timedelta(days=3)
    return start.isoformat(), end.isoformat()


# ---- F.R 1.4 — customer cannot reach admin endpoints ----
def test_customer_token_rejected_on_admin_endpoints(app_client):
    tok = _register_customer(app_client)
    for path in ("/admin/dashboard", "/admin/vehicles", "/admin/categories", "/admin/bookings"):
        r = app_client.get(path, headers=_auth(tok))
        assert r.status_code == 403, f"{path}: {r.status_code}"


# ---- F.R 5.1 / 5.2 — vehicle CRUD + status cascade behavior ----
def test_admin_vehicle_lifecycle_and_catalog_filter(app_client):
    admin = make_admin(app_client)
    tok = admin["token"]

    # list
    r = app_client.get("/admin/vehicles", headers=_auth(tok))
    assert r.status_code == 200
    initial = r.json()
    assert len(initial) == 2  # seeded

    # create
    r = app_client.post(
        "/admin/vehicles",
        json={
            "vin": "VINADMIN1",
            "make": "Ford",
            "model": "F150",
            "year": 2024,
            "seats": 5,
            "status": "AVAILABLE",
            "category_id": initial[0]["category_id"],
            "home_location_id": initial[0]["home_location_id"],
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["vin"] == "VINADMIN1"

    # patch to IN_MAINTENANCE
    r = app_client.patch(
        f"/admin/vehicles/{created['id']}",
        json={"status": "IN_MAINTENANCE"},
        headers=_auth(tok),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "IN_MAINTENANCE"

    # catalog /vehicles must not return the maintenance one
    r = app_client.get("/vehicles")
    ids = [v["id"] for v in r.json()]
    assert created["id"] not in ids


# ---- F.R 5.3 — category rate change does NOT alter existing booking totals ----
def test_category_rate_change_does_not_alter_existing_booking(app_client):
    # customer books a vehicle; capture quote_total
    ctok = _register_customer(app_client)
    r = app_client.get("/vehicles")
    v = r.json()[0]
    start, end = _window()
    r = app_client.post(
        "/bookings",
        json={
            "vehicle_id": v["id"],
            "period_start": start,
            "period_end": end,
            "pickup_location_id": v["home_location_id"],
            "return_location_id": v["home_location_id"],
        },
        headers=_auth(ctok),
    )
    assert r.status_code == 201, r.text
    booking = r.json()
    original_total = float(booking["quote_total"])

    # admin updates the category rates
    admin = make_admin(app_client)
    atok = admin["token"]
    cat_id = v["category_id"]
    r = app_client.patch(
        f"/admin/categories/{cat_id}",
        json={"daily_rate": "999.00", "flat_fee": "500.00"},
        headers=_auth(atok),
    )
    assert r.status_code == 200
    assert float(r.json()["daily_rate"]) == 999.0

    # existing booking total unchanged (snapshot preserved)
    r = app_client.get("/admin/bookings", headers=_auth(atok))
    rows = [b for b in r.json() if b["id"] == booking["id"]]
    assert rows and float(rows[0]["quote_total"]) == original_total


# ---- F.R 5.4 — override status + audit entry ----
def test_override_status_writes_audit_entry(app_client):
    ctok = _register_customer(app_client)
    r = app_client.get("/vehicles")
    v = r.json()[0]
    start, end = _window()
    r = app_client.post(
        "/bookings",
        json={
            "vehicle_id": v["id"],
            "period_start": start,
            "period_end": end,
            "pickup_location_id": v["home_location_id"],
            "return_location_id": v["home_location_id"],
        },
        headers=_auth(ctok),
    )
    booking_id = r.json()["id"]

    admin = make_admin(app_client)
    atok = admin["token"]
    r = app_client.post(
        f"/admin/bookings/{booking_id}/override-status",
        json={"status": "COMPLETED", "reason": "manual close by admin"},
        headers=_auth(atok),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "COMPLETED"

    # verify audit_entries row exists
    from app import db as _db
    from app.admin.service import AuditEntry
    with _db.SessionLocal() as s:
        rows = s.query(AuditEntry).filter(AuditEntry.action == "admin_override_status").all()
        assert len(rows) == 1
        assert rows[0].actor == admin["user_id"]
        assert rows[0].before["status"] == "INPROGRESS"
        assert rows[0].after["status"] == "COMPLETED"
        assert rows[0].after["reason"] == "manual close by admin"


# ---- F.R 5.5 — dashboard aggregates ----
def test_dashboard_returns_counts(app_client):
    admin = make_admin(app_client)
    r = app_client.get("/admin/dashboard", headers=_auth(admin["token"]))
    assert r.status_code == 200
    body = r.json()
    # 2 seeded vehicles, both AVAILABLE
    assert body["counts"]["total"] == 2
    assert body["counts"]["available"] == 2
    assert body["counts"]["rented"] == 0
    assert body["bookings_by_status"]["INPROGRESS"] == 0
    assert body["upcoming_pickups_7d"] == 0
    assert float(body["revenue_30d"]) == 0.0


# ---- Bonus — bookings search filter by vehicle_id ----
def test_bookings_search_filters(app_client):
    ctok = _register_customer(app_client)
    r = app_client.get("/vehicles")
    v = r.json()[0]
    start, end = _window()
    app_client.post(
        "/bookings",
        json={
            "vehicle_id": v["id"],
            "period_start": start,
            "period_end": end,
            "pickup_location_id": v["home_location_id"],
            "return_location_id": v["home_location_id"],
        },
        headers=_auth(ctok),
    )
    admin = make_admin(app_client)
    atok = admin["token"]
    r = app_client.get(f"/admin/bookings?vehicle_id={v['id']}", headers=_auth(atok))
    assert r.status_code == 200
    assert len(r.json()) == 1
    r = app_client.get("/admin/bookings?status=CONFIRMED", headers=_auth(atok))
    assert r.json() == []
