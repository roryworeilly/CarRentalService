"""Booking service — quote, create hold, pay, cancel, expire.

Requirements:
  - F.R 1.1: enforce age >=21 and unexpired licence on booking creation.
  - F.R 3.1: quoting prior to booking.
  - F.R 3.2: cost = daily_rate * days + flat_fee - subscription discount.
  - F.R 3.3: new booking enters INPROGRESS, removing vehicle from search.
  - F.R 3.5: cancellation prior to pickup.
  - F.R 4.1/4.3: pay → CONFIRMED on success.
  - F.R 4.4: on payment failure → FAILED_PAYMENT, hold_expires_at = now + 15m.
  - F.R 4.5: refund only from CONFIRMED.
  - NFR 3: subscription discount.
"""
from __future__ import annotations

import math
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Booking, Payment, Refund, User, Vehicle, VehicleCategory, DriverLicence, Subscription
from ..payments.gateway import MockGateway

LIVE_STATUSES = ("INPROGRESS", "CONFIRMED", "FAILED_PAYMENT")
_settings = get_settings()


# ---- helpers ----
def _q(d) -> Decimal:
    return Decimal(d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _days(start: datetime, end: datetime) -> int:
    if end <= start:
        raise HTTPException(400, "period_end must be after period_start")
    delta = end - start
    return max(1, math.ceil(delta.total_seconds() / 86400))


def _age(dob: date) -> int:
    t = date.today()
    return t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))


def _calc(daily_rate, days: int, flat_fee, discount_pct) -> dict:
    daily_rate = Decimal(daily_rate)
    flat_fee = Decimal(flat_fee)
    discount_pct = Decimal(discount_pct or 0)
    subtotal = (daily_rate * days) + flat_fee
    total = subtotal * (Decimal(1) - discount_pct / Decimal(100))
    return {
        "daily_rate": _q(daily_rate),
        "days": days,
        "flat_fee": _q(flat_fee),
        "discount_pct": _q(discount_pct),
        "subtotal": _q(subtotal),
        "total": _q(total),
    }


def _vehicle_with_category(db: Session, vehicle_id: str) -> tuple[Vehicle, VehicleCategory]:
    row = db.execute(
        select(Vehicle, VehicleCategory).join(VehicleCategory, Vehicle.category_id == VehicleCategory.id)
        .where(Vehicle.id == vehicle_id)
    ).first()
    if not row:
        raise HTTPException(404, "vehicle not found")
    return row[0], row[1]


def _subscription_discount(db: Session, user_id: str) -> Decimal:
    sub = db.get(Subscription, user_id)
    if not sub:
        return Decimal(0)
    today = date.today()
    if sub.starts_on > today or (sub.ends_on and sub.ends_on < today):
        return Decimal(0)
    return Decimal(sub.discount_pct or 0)


# ---- quote ----
def quote(db: Session, *, vehicle_id: str, period_start: datetime, period_end: datetime, user: User) -> dict:
    _, cat = _vehicle_with_category(db, vehicle_id)
    days = _days(period_start, period_end)
    discount = _subscription_discount(db, user.id)
    q = _calc(cat.daily_rate, days, cat.flat_fee, discount)
    return {"vehicle_id": vehicle_id, **q}


# ---- create (INPROGRESS hold) ----
def create_booking(
    db: Session,
    *,
    user: User,
    vehicle_id: str,
    period_start: datetime,
    period_end: datetime,
    pickup_location_id: int,
    return_location_id: int,
) -> Booking:
    # F.R 1.1 — eligibility at booking time.
    if user.date_of_birth is None or _age(user.date_of_birth) < 21:
        raise HTTPException(403, "customer must be 21+ to book")
    lic = db.get(DriverLicence, user.id)
    if lic is None:
        raise HTTPException(403, "driver licence required")
    if lic.expires_on < date.today():
        raise HTTPException(403, "driver licence expired")

    vehicle, cat = _vehicle_with_category(db, vehicle_id)
    if vehicle.status != "AVAILABLE":
        raise HTTPException(409, "vehicle not available")

    # App-level overlap guard (Postgres EXCLUDE is the hard guarantee → 409).
    overlap = db.execute(
        select(Booking.id).where(
            and_(
                Booking.vehicle_id == vehicle_id,
                Booking.status.in_(LIVE_STATUSES),
                Booking.period_start < period_end,
                Booking.period_end > period_start,
            )
        )
    ).first()
    if overlap:
        raise HTTPException(409, "vehicle already booked for that period")

    days = _days(period_start, period_end)
    discount = _subscription_discount(db, user.id)
    q = _calc(cat.daily_rate, days, cat.flat_fee, discount)

    booking = Booking(
        reference=f"BK-{secrets.token_hex(4).upper()}",
        customer_id=user.id,
        vehicle_id=vehicle_id,
        status="INPROGRESS",  # F.R 3.3
        period_start=period_start,
        period_end=period_end,
        pickup_location_id=pickup_location_id,
        return_location_id=return_location_id,
        quote_daily_rate=q["daily_rate"],
        quote_days=q["days"],
        quote_flat_fee=q["flat_fee"],
        quote_discount_pct=q["discount_pct"],
        quote_subtotal=q["subtotal"],
        quote_total=q["total"],
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    _notify(booking, "booking_created")
    return booking


# ---- pay ----
def pay(db: Session, *, booking_id: str, user: User, card_number: str, idempotency_key: str) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "booking not found")
    if booking.customer_id != user.id:
        raise HTTPException(403, "not your booking")
    if booking.status not in ("INPROGRESS", "FAILED_PAYMENT"):
        raise HTTPException(409, f"cannot pay a {booking.status} booking")

    gw = MockGateway()
    result = gw.charge(card_number=card_number, amount=float(booking.quote_total), idempotency_key=idempotency_key)

    payment = Payment(
        booking_id=booking.id,
        gateway_intent_id=result.intent_id,
        idempotency_key=idempotency_key,
        amount=booking.quote_total,
        status="SUCCEEDED" if result.success else "FAILED",
        card_last4=result.last4,
    )
    db.add(payment)

    if result.success:
        # F.R 4.3
        booking.status = "CONFIRMED"
        booking.hold_expires_at = None
        db.commit()
        db.refresh(booking)
        _notify(booking, "booking_confirmed")
        return booking

    # F.R 4.4 — hold timer starts on payment failure.
    booking.status = "FAILED_PAYMENT"
    booking.hold_expires_at = datetime.now(timezone.utc) + timedelta(minutes=_settings.HOLD_WINDOW_MINUTES)
    db.commit()
    db.refresh(booking)
    _notify(booking, "payment_failed")
    raise HTTPException(status_code=402, detail={
        "message": "payment failed",
        "booking_status": booking.status,
        "hold_expires_at": booking.hold_expires_at.isoformat(),
    })


# ---- cancel ----
def cancel(db: Session, *, booking_id: str, user: User) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "booking not found")
    if booking.customer_id != user.id:
        raise HTTPException(403, "not your booking")
    if booking.status not in ("INPROGRESS", "CONFIRMED"):
        raise HTTPException(409, f"cannot cancel a {booking.status} booking")
    now = datetime.now(timezone.utc)
    # Normalize for naive comparisons from sqlite
    period_start = booking.period_start
    if period_start.tzinfo is None:
        period_start = period_start.replace(tzinfo=timezone.utc)
    if period_start <= now:
        raise HTTPException(409, "cannot cancel after pickup")

    prior_status = booking.status
    booking.status = "CANCELLED"
    booking.hold_expires_at = None

    # F.R 4.5 — refund only when cancelling a CONFIRMED (paid) booking.
    if prior_status == "CONFIRMED":
        last_pay = db.execute(
            select(Payment).where(and_(Payment.booking_id == booking.id, Payment.status == "SUCCEEDED"))
            .order_by(Payment.attempted_at.desc())
        ).scalars().first()
        if last_pay:
            db.add(Refund(payment_id=last_pay.id, amount=last_pay.amount, reason="customer cancellation"))
            last_pay.status = "REFUNDED"
    db.commit()
    db.refresh(booking)
    _notify(booking, "booking_cancelled")
    return booking


# ---- list ----
def list_for_user(db: Session, *, user: User) -> list[Booking]:
    rows = db.execute(select(Booking).where(Booking.customer_id == user.id).order_by(Booking.created_at.desc())).scalars().all()
    return list(rows)


# ---- expiry sweep (F.R 4.4) ----
def expire_stale_holds(db: Session) -> int:
    """Transition FAILED_PAYMENT bookings past their hold window to EXPIRED.

    Returns the number of bookings expired. Intended to be called by a scheduler
    in production; the prototype only exposes the function.
    """
    now = datetime.now(timezone.utc)
    stale = db.execute(
        select(Booking).where(and_(Booking.status == "FAILED_PAYMENT", Booking.hold_expires_at.is_not(None)))
    ).scalars().all()
    count = 0
    for b in stale:
        exp = b.hold_expires_at
        if exp is not None and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp is not None and exp <= now:
            b.status = "EXPIRED"
            b.hold_expires_at = None
            count += 1
    if count:
        db.commit()
    return count


# ---- email stub (F.R 4.2) ----
def _notify(booking: Booking, template: str) -> None:
    print(f"[notification] template={template} booking={booking.reference} status={booking.status}")
