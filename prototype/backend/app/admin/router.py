"""Admin router. F.R 5.1-5.5 / UC-19..UC-23.

All endpoints require an ADMIN token via require_role('ADMIN') — F.R 1.4.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_role
from ..models import User, Vehicle
from ..schemas import (
    AdminDashboard,
    AdminVehicleOut,
    AdminBookingOut,
    BookingOverrideRequest,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    VehicleCreate,
    VehicleUpdate,
)
from . import service

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- Dashboard (F.R 5.5 / UC-22) ----
@router.get("/dashboard", response_model=AdminDashboard)
def get_dashboard(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return service.dashboard(db)


# ---- Vehicles (F.R 5.1, 5.2) ----
@router.get("/vehicles", response_model=list[AdminVehicleOut])
def list_vehicles(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return service.list_vehicles(db)


@router.post("/vehicles", response_model=AdminVehicleOut, status_code=201)
def create_vehicle(body: VehicleCreate, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return service.create_vehicle(db, body.model_dump())


@router.patch("/vehicles/{vehicle_id}", response_model=AdminVehicleOut)
def update_vehicle(
    vehicle_id: str,
    body: VehicleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    return service.update_vehicle(db, vehicle_id, body.model_dump(exclude_unset=True))


# ---- Categories (F.R 5.3) ----
@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return service.list_categories(db)


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    return service.create_category(db, body.model_dump())


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    # F.R 5.3: PriceQuote snapshot on Booking means existing bookings keep their totals.
    return service.update_category(db, category_id, body.model_dump(exclude_unset=True))


# ---- Bookings (F.R 5.4 / UC-21) ----
def _enrich(db: Session, b) -> AdminBookingOut:
    """Attach customer email and vehicle label so the admin table can show them."""
    out = AdminBookingOut.model_validate(b)
    cust = db.get(User, b.customer_id)
    veh = db.get(Vehicle, b.vehicle_id)
    out.customer_email = cust.email if cust else None
    out.vehicle_label = f"{veh.make} {veh.model}" if veh else None
    return out


@router.get("/bookings", response_model=list[AdminBookingOut])
def search_bookings(
    status: Optional[str] = Query(None),
    customer_email: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    from_: Optional[datetime] = Query(None, alias="from"),
    to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    rows = service.search_bookings(
        db,
        status=status,
        customer_email=customer_email,
        vehicle_id=vehicle_id,
        from_=from_,
        to=to,
    )
    return [_enrich(db, b) for b in rows]


@router.post("/bookings/{booking_id}/override-status", response_model=AdminBookingOut)
def override_booking_status(
    booking_id: str,
    body: BookingOverrideRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("ADMIN")),
):
    b = service.override_status(
        db,
        booking_id=booking_id,
        new_status=body.status,
        reason=body.reason,
        actor=actor,
    )
    return _enrich(db, b)
