"""SQLAlchemy ORM models mapped to prototype/db/schema.sql.

Note: schema.sql uses Postgres-specific types (uuid, tstzrange, EXCLUDE, enums).
For portability (sqlite tests), uuids are CHAR(36), enums are strings, and the
`period` tstzrange is modelled as `period_start`/`period_end` timestamp columns.
When running against the real Postgres schema, bind manually with care — the
prototype assumes `Base.metadata.create_all` is only used for tests/dev.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, time
from typing import Optional

from sqlalchemy import (
    String, Integer, Text, Boolean, Date, Time, DateTime, Numeric,
    ForeignKey, CHAR,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="CUSTOMER")
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    first_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[Optional[str]] = mapped_column(Text)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    staff_id: Mapped[Optional[str]] = mapped_column(Text)

    licence: Mapped[Optional["DriverLicence"]] = relationship(back_populates="user", uselist=False)
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", uselist=False)


class DriverLicence(Base):
    __tablename__ = "driver_licences"
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    number: Mapped[str] = mapped_column(Text, nullable=False)
    issuing_state: Mapped[str] = mapped_column(Text, nullable=False)
    expires_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="licence")


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tier: Mapped[str] = mapped_column(String(16), nullable=False, default="NONE")
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[Optional[date]] = mapped_column(Date)

    user: Mapped[User] = relationship(back_populates="subscription")


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    opens_at: Mapped[time] = mapped_column(Time, nullable=False)
    closes_at: Mapped[time] = mapped_column(Time, nullable=False)


class VehicleCategory(Base):
    __tablename__ = "vehicle_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    daily_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    flat_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    vin: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    make: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="AVAILABLE")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicle_categories.id"), nullable=False)
    home_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)

    category: Mapped[VehicleCategory] = relationship()
    home_location: Mapped[Location] = relationship()


class VehicleImage(Base):
    __tablename__ = "vehicle_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Booking(Base):
    """F.R 3.1-3.5. On Postgres the real schema uses a `period tstzrange`
    column; here we expose two timestamp columns `period_start`/`period_end`
    for app-level use. On Postgres, EXCLUDE enforces no-overlap and surfaces
    as IntegrityError → 409 via the global handler.
    """
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    reference: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("vehicles.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="INPROGRESS")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pickup_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    return_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    hold_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    # Snapshot of PriceQuote (F.R 3.2, prevents retroactive rate changes)
    quote_daily_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quote_flat_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    quote_subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("bookings.id"), nullable=False)
    gateway_intent_id: Mapped[Optional[str]] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    card_last4: Mapped[Optional[str]] = mapped_column(CHAR(4))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Refund(Base):
    __tablename__ = "refunds"
    payment_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey("payments.id"), primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
