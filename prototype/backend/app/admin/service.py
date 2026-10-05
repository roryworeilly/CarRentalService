"""Admin service — fleet dashboard, vehicle/category CRUD, booking override.

Requirements:
  - F.R 5.1 / 5.2: CRUD vehicles including status (AVAILABLE/RENTED/IN_MAINTENANCE/RETIRED).
  - F.R 5.3: category & rate management. Rate changes DO NOT retro-affect existing bookings
    because PriceQuote is snapshotted on Booking at creation time (see models.Booking).
  - F.R 5.4 / UC-21: search bookings + override status, with an audit_entries row.
  - F.R 5.5 / UC-22: fleet dashboard aggregates.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, CHAR, func, select, and_
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from ..db import Base
from ..models import Booking, User, Vehicle, VehicleCategory, Location


# ---- AuditEntry ORM model (matches schema.sql audit_entries table). ----
# Declared here (not in models.py) to keep the admin module self-contained; registered
# on the same Base so Base.metadata.create_all() in tests sees it.
class AuditEntry(Base):
    __tablename__ = "audit_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[Optional[str]] = mapped_column(CHAR(36), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    before: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    after: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


VEHICLE_STATUSES = {"AVAILABLE", "RENTED", "IN_MAINTENANCE", "RETIRED"}
BOOKING_STATUSES = {"INPROGRESS", "CONFIRMED", "FAILED_PAYMENT", "EXPIRED", "CANCELLED", "COMPLETED"}


# ---- Dashboard (F.R 5.5) ----
def dashboard(db: Session) -> dict:
    counts = {s: 0 for s in ("available", "rented", "in_maintenance", "retired")}
    rows = db.execute(select(Vehicle.status, func.count(Vehicle.id)).group_by(Vehicle.status)).all()
    total = 0
    for status, n in rows:
        total += n
        key = status.lower()
        if key in counts:
            counts[key] = n
    counts["total"] = total

    by_status = {s: 0 for s in BOOKING_STATUSES}
    for status, n in db.execute(select(Booking.status, func.count(Booking.id)).group_by(Booking.status)).all():
        if status in by_status:
            by_status[status] = n

    now = datetime.now(timezone.utc)
    week_ahead = now + timedelta(days=7)
    upcoming = db.execute(
        select(func.count(Booking.id)).where(
            and_(
                Booking.status == "CONFIRMED",
                Booking.period_start >= now,
                Booking.period_start <= week_ahead,
            )
        )
    ).scalar() or 0

    thirty_ago = now - timedelta(days=30)
    revenue = db.execute(
        select(func.coalesce(func.sum(Booking.quote_total), 0)).where(
            and_(
                Booking.status.in_(("CONFIRMED", "COMPLETED")),
                Booking.period_start >= thirty_ago,
            )
        )
    ).scalar() or 0

    return {
        "counts": counts,
        "bookings_by_status": by_status,
        "upcoming_pickups_7d": int(upcoming),
        "revenue_30d": Decimal(revenue),
    }


# ---- Vehicles (F.R 5.1, 5.2) ----
def list_vehicles(db: Session) -> list[dict]:
    rows = db.execute(
        select(Vehicle, VehicleCategory, Location)
        .join(VehicleCategory, Vehicle.category_id == VehicleCategory.id)
        .join(Location, Vehicle.home_location_id == Location.id)
    ).all()
    return [_vehicle_row(v, c, loc) for v, c, loc in rows]


def _vehicle_row(v: Vehicle, c: VehicleCategory, loc: Location) -> dict:
    return {
        "id": v.id,
        "vin": v.vin,
        "make": v.make,
        "model": v.model,
        "year": v.year,
        "seats": v.seats,
        "status": v.status,
        "category_id": v.category_id,
        "home_location_id": v.home_location_id,
        "category_name": c.name,
        "location_code": loc.code,
    }


def create_vehicle(db: Session, data: dict) -> dict:
    if data["status"] not in VEHICLE_STATUSES:
        raise HTTPException(400, f"invalid status; must be one of {sorted(VEHICLE_STATUSES)}")
    if db.get(VehicleCategory, data["category_id"]) is None:
        raise HTTPException(400, "category_id not found")
    if db.get(Location, data["home_location_id"]) is None:
        raise HTTPException(400, "home_location_id not found")
    v = Vehicle(
        vin=data["vin"],
        make=data["make"],
        model=data["model"],
        year=data["year"],
        seats=data["seats"],
        status=data["status"],
        category_id=data["category_id"],
        home_location_id=data["home_location_id"],
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    c = db.get(VehicleCategory, v.category_id)
    loc = db.get(Location, v.home_location_id)
    return _vehicle_row(v, c, loc)


def update_vehicle(db: Session, vehicle_id: str, patch: dict) -> dict:
    v = db.get(Vehicle, vehicle_id)
    if v is None:
        raise HTTPException(404, "vehicle not found")
    # F.R 5.1: status change to IN_MAINTENANCE / RETIRED does NOT cascade to live bookings;
    # existing bookings remain intact. The catalog search already filters by status==AVAILABLE,
    # so new reservations are blocked automatically.
    if "status" in patch and patch["status"] is not None:
        if patch["status"] not in VEHICLE_STATUSES:
            raise HTTPException(400, f"invalid status; must be one of {sorted(VEHICLE_STATUSES)}")
    for field in ("vin", "make", "model", "year", "seats", "status", "category_id", "home_location_id"):
        if field in patch and patch[field] is not None:
            setattr(v, field, patch[field])
    db.commit()
    db.refresh(v)
    c = db.get(VehicleCategory, v.category_id)
    loc = db.get(Location, v.home_location_id)
    return _vehicle_row(v, c, loc)


# ---- Categories (F.R 5.3) ----
def list_categories(db: Session) -> list[VehicleCategory]:
    return list(db.execute(select(VehicleCategory)).scalars().all())


def create_category(db: Session, data: dict) -> VehicleCategory:
    cat = VehicleCategory(name=data["name"], daily_rate=data["daily_rate"], flat_fee=data["flat_fee"])
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, category_id: int, patch: dict) -> VehicleCategory:
    # F.R 5.3: rate changes update ONLY the category row. Existing Booking rows carry a
    # PriceQuote snapshot (quote_daily_rate / quote_flat_fee / quote_total) so their totals
    # are not affected retroactively — see models.Booking docstring.
    cat = db.get(VehicleCategory, category_id)
    if cat is None:
        raise HTTPException(404, "category not found")
    for field in ("name", "daily_rate", "flat_fee"):
        if field in patch and patch[field] is not None:
            setattr(cat, field, patch[field])
    db.commit()
    db.refresh(cat)
    return cat


# ---- Bookings (F.R 5.4) ----
def search_bookings(
    db: Session,
    *,
    status: Optional[str] = None,
    customer_email: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    from_: Optional[datetime] = None,
    to: Optional[datetime] = None,
) -> list[Booking]:
    q = select(Booking)
    if status:
        q = q.where(Booking.status == status)
    if vehicle_id:
        q = q.where(Booking.vehicle_id == vehicle_id)
    if customer_email:
        q = q.join(User, Booking.customer_id == User.id).where(User.email == customer_email)
    if from_:
        q = q.where(Booking.period_start >= from_)
    if to:
        q = q.where(Booking.period_end <= to)
    q = q.order_by(Booking.created_at.desc())
    return list(db.execute(q).scalars().all())


def _booking_snapshot(b: Booking) -> dict:
    return {
        "id": b.id,
        "reference": b.reference,
        "status": b.status,
        "customer_id": b.customer_id,
        "vehicle_id": b.vehicle_id,
    }


def override_status(db: Session, *, booking_id: str, new_status: str, reason: str, actor: User) -> Booking:
    if new_status not in BOOKING_STATUSES:
        raise HTTPException(400, f"invalid status; must be one of {sorted(BOOKING_STATUSES)}")
    b = db.get(Booking, booking_id)
    if b is None:
        raise HTTPException(404, "booking not found")
    before = _booking_snapshot(b)
    b.status = new_status
    if new_status not in ("FAILED_PAYMENT",):
        b.hold_expires_at = None
    after = {**_booking_snapshot(b), "reason": reason}
    db.add(AuditEntry(actor=actor.id, action="admin_override_status", before=before, after=after))
    db.commit()
    db.refresh(b)
    return b
