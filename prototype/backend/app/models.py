"""SQLAlchemy ORM models mapped to prototype/db/schema.sql.

Note: schema.sql uses Postgres-specific types (uuid, tstzrange, EXCLUDE, enums).
These models target BOTH engines via dialect variants:
  * ids: native `uuid` on Postgres (as_uuid=False -> python str), CHAR(36) on sqlite.
  * enums: native Postgres enums (create_type=False; schema.sql owns them), String on sqlite.
  * bookings.period: `tstzrange` on Postgres; "start|end" text on sqlite. The app uses
    `Booking.period_start` / `Booking.period_end` (hybrid properties, SQL lower()/upper()
    on Postgres) so service code is identical on both engines.
On Postgres, schema.sql (not create_all) creates the schema.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, time, timezone
from typing import Optional

from sqlalchemy import (
    String, Integer, Text, Boolean, Date, Time, DateTime, Numeric,
    ForeignKey, CHAR,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# ---- dialect-portable column types ----
IdType = CHAR(36).with_variant(postgresql.UUID(as_uuid=False), "postgresql")


def _enum(name: str, *values: str):
    return String(16).with_variant(
        postgresql.ENUM(*values, name=name, create_type=False), "postgresql"
    )


RoleType = _enum("role", "CUSTOMER", "ADMIN")
VehicleStatusType = _enum("vehicle_status", "AVAILABLE", "RENTED", "IN_MAINTENANCE", "RETIRED")
BookingStatusType = _enum(
    "booking_status", "INPROGRESS", "CONFIRMED", "FAILED_PAYMENT", "EXPIRED", "CANCELLED", "COMPLETED"
)
PaymentStatusType = _enum("payment_status", "PENDING", "SUCCEEDED", "FAILED", "REFUNDED")
SubTierType = _enum("sub_tier", "NONE", "STANDARD", "PREMIUM")

_SQLITE_FMT = "%Y-%m-%d %H:%M:%S.%f"  # 26 chars, same layout sqlite DateTime uses


class PeriodType(TypeDecorator):
    """Python side: (start, end) tuple of datetimes, half-open [start, end).
    Postgres: tstzrange. sqlite: 'start|end' text (for tests)."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.TSTZRANGE())
        return dialect.type_descriptor(String(53))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        start, end = value
        if dialect.name == "postgresql":
            return postgresql.Range(start, end, bounds="[)")
        return f"{start.strftime(_SQLITE_FMT)}|{end.strftime(_SQLITE_FMT)}"

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return (value.lower, value.upper)
        a, b = value.split("|")
        return (datetime.strptime(a, _SQLITE_FMT), datetime.strptime(b, _SQLITE_FMT))


class _PeriodBound(FunctionElement):
    inherit_cache = True
    type = DateTime(timezone=True)

    def __init__(self, col, which: str):
        self.which = which
        super().__init__(col)


@compiles(_PeriodBound)
def _bound_default(element, compiler, **kw):  # sqlite
    col = compiler.process(element.clauses.clauses[0], **kw)
    return f"substr({col}, 1, 26)" if element.which == "lower" else f"substr({col}, 28)"


@compiles(_PeriodBound, "postgresql")
def _bound_pg(element, compiler, **kw):
    col = compiler.process(element.clauses.clauses[0], **kw)
    return f"{element.which}({col})"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(IdType, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(RoleType, nullable=False, default="CUSTOMER")
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    first_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[Optional[str]] = mapped_column(Text)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    staff_id: Mapped[Optional[str]] = mapped_column(Text)

    licence: Mapped[Optional["DriverLicence"]] = relationship(back_populates="user", uselist=False)
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", uselist=False)


class DriverLicence(Base):
    __tablename__ = "driver_licences"
    user_id: Mapped[str] = mapped_column(IdType, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    number: Mapped[str] = mapped_column(Text, nullable=False)
    issuing_state: Mapped[str] = mapped_column(Text, nullable=False)
    expires_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="licence")


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[str] = mapped_column(IdType, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tier: Mapped[str] = mapped_column(SubTierType, nullable=False, default="NONE")
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
    id: Mapped[str] = mapped_column(IdType, primary_key=True, default=_uuid)
    vin: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    make: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(VehicleStatusType, nullable=False, default="AVAILABLE")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicle_categories.id"), nullable=False)
    home_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)

    category: Mapped[VehicleCategory] = relationship()
    home_location: Mapped[Location] = relationship()


class VehicleImage(Base):
    __tablename__ = "vehicle_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(IdType, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Booking(Base):
    """F.R 3.1-3.5. On Postgres the real schema uses a `period tstzrange`
    column; here we expose two timestamp columns `period_start`/`period_end`
    for app-level use. On Postgres, EXCLUDE enforces no-overlap and surfaces
    as IntegrityError → 409 via the global handler.
    """
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(IdType, primary_key=True, default=_uuid)
    reference: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(IdType, ForeignKey("users.id"), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(IdType, ForeignKey("vehicles.id"), nullable=False)
    status: Mapped[str] = mapped_column(BookingStatusType, nullable=False, default="INPROGRESS")
    period: Mapped[tuple] = mapped_column(PeriodType, nullable=False)
    pickup_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    return_location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    hold_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # Snapshot of PriceQuote (F.R 3.2, prevents retroactive rate changes)
    quote_daily_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quote_flat_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    quote_subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quote_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # period_start / period_end: python view + SQL expression over `period`.
    @hybrid_property
    def period_start(self) -> Optional[datetime]:
        return self.period[0] if self.period else None

    @period_start.inplace.setter
    def _period_start_set(self, value: datetime) -> None:
        self.period = (value, self.period[1] if self.period else None)

    @period_start.inplace.expression
    @classmethod
    def _period_start_expr(cls):
        return _PeriodBound(cls.period, "lower")

    @hybrid_property
    def period_end(self) -> Optional[datetime]:
        return self.period[1] if self.period else None

    @period_end.inplace.setter
    def _period_end_set(self, value: datetime) -> None:
        self.period = (self.period[0] if self.period else None, value)

    @period_end.inplace.expression
    @classmethod
    def _period_end_expr(cls):
        return _PeriodBound(cls.period, "upper")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(IdType, primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(IdType, ForeignKey("bookings.id"), nullable=False)
    gateway_intent_id: Mapped[Optional[str]] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(PaymentStatusType, nullable=False, default="PENDING")
    card_last4: Mapped[Optional[str]] = mapped_column(CHAR(4))
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Refund(Base):
    __tablename__ = "refunds"
    payment_id: Mapped[str] = mapped_column(IdType, ForeignKey("payments.id"), primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
