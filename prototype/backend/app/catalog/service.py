"""Vehicle catalog service. F.R 2.1-2.4."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from ..models import Vehicle, VehicleCategory, Booking


LIVE_STATUSES = ("INPROGRESS", "CONFIRMED", "FAILED_PAYMENT")


def search_vehicles(
    db: Session,
    *,
    category: Optional[str] = None,
    location_id: Optional[int] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
):
    """Only AVAILABLE vehicles and those with no overlapping live booking.
    F.R 2.4 — a vehicle currently held/reserved cannot appear in results.
    """
    q = select(Vehicle, VehicleCategory).join(VehicleCategory, Vehicle.category_id == VehicleCategory.id)
    q = q.where(Vehicle.status == "AVAILABLE")

    if category:
        q = q.where(VehicleCategory.name == category)
    if location_id is not None:
        q = q.where(Vehicle.home_location_id == location_id)

    rows = db.execute(q).all()

    if period_start and period_end:
        # Exclude vehicles with any live overlapping booking.
        overlap_q = select(Booking.vehicle_id).where(
            and_(
                Booking.status.in_(LIVE_STATUSES),
                Booking.period_start < period_end,
                Booking.period_end > period_start,
            )
        )
        booked_ids = {row[0] for row in db.execute(overlap_q).all()}
        rows = [r for r in rows if r[0].id not in booked_ids]

    return [
        {
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
            "daily_rate": c.daily_rate,
            "flat_fee": c.flat_fee,
        }
        for v, c in rows
    ]


def get_vehicle(db: Session, vehicle_id: str):
    """Return a single vehicle with category info. F.R 2.1."""
    row = db.execute(
        select(Vehicle, VehicleCategory)
        .join(VehicleCategory, Vehicle.category_id == VehicleCategory.id)
        .where(Vehicle.id == vehicle_id)
    ).first()
    if row is None:
        return None
    v, c = row
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
        "daily_rate": c.daily_rate,
        "flat_fee": c.flat_fee,
    }
