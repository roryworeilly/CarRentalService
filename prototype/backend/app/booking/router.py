"""Booking router. F.R 3.x / 4.x."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_role
from ..models import User
from ..schemas import BookingCreateIn, BookingOut, PaymentIn, QuoteIn, QuoteOut
from . import service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/quote", response_model=QuoteOut)
def quote(body: QuoteIn, db: Session = Depends(get_db), user: User = Depends(require_role("CUSTOMER"))):
    return service.quote(db, vehicle_id=body.vehicle_id, period_start=body.period_start, period_end=body.period_end, user=user)


@router.post("", response_model=BookingOut, status_code=201)
def create(body: BookingCreateIn, db: Session = Depends(get_db), user: User = Depends(require_role("CUSTOMER"))):
    return service.create_booking(
        db,
        user=user,
        vehicle_id=body.vehicle_id,
        period_start=body.period_start,
        period_end=body.period_end,
        pickup_location_id=body.pickup_location_id,
        return_location_id=body.return_location_id,
    )


@router.post("/{booking_id}/pay", response_model=BookingOut)
def pay(booking_id: str, body: PaymentIn, db: Session = Depends(get_db), user: User = Depends(require_role("CUSTOMER"))):
    return service.pay(db, booking_id=booking_id, user=user, card_number=body.card_number, idempotency_key=body.idempotency_key)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel(booking_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("CUSTOMER"))):
    return service.cancel(db, booking_id=booking_id, user=user)


@router.get("", response_model=list[BookingOut])
def list_mine(db: Session = Depends(get_db), user: User = Depends(require_role("CUSTOMER"))):
    """F.R 3.4 — customer sees their own bookings. require_role('CUSTOMER')
    enforces F.R 1.4: admin tokens cannot access this endpoint.
    """
    return service.list_for_user(db, user=user)
