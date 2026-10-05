"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---- Auth ----
class LicenceIn(BaseModel):
    number: str
    issuing_state: str
    expires_on: date


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    last_name: str
    date_of_birth: date
    phone: Optional[str] = None
    licence: LicenceIn  # F.R 1.1: licence required at registration


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    role: str
    user_id: str


# ---- Catalog ----
class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    vin: str
    make: str
    model: str
    year: int
    seats: int
    status: str
    category_id: int
    home_location_id: int


class VehicleSearchOut(VehicleOut):
    category_name: str
    daily_rate: Decimal
    flat_fee: Decimal


# ---- Booking ----
class QuoteIn(BaseModel):
    vehicle_id: str
    period_start: datetime
    period_end: datetime


class QuoteOut(BaseModel):
    vehicle_id: str
    daily_rate: Decimal
    days: int
    flat_fee: Decimal
    discount_pct: Decimal
    subtotal: Decimal
    total: Decimal


class BookingCreateIn(BaseModel):
    vehicle_id: str
    period_start: datetime
    period_end: datetime
    pickup_location_id: int
    return_location_id: int


class PaymentIn(BaseModel):
    card_number: str = Field(min_length=12, max_length=19)
    exp_month: int = Field(ge=1, le=12)
    exp_year: int
    cvc: str = Field(min_length=3, max_length=4)
    idempotency_key: str


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    reference: str
    customer_id: str
    vehicle_id: str
    status: str
    period_start: datetime
    period_end: datetime
    pickup_location_id: int
    return_location_id: int
    hold_expires_at: Optional[datetime]
    quote_daily_rate: Decimal
    quote_days: int
    quote_flat_fee: Decimal
    quote_discount_pct: Decimal
    quote_subtotal: Decimal
    quote_total: Decimal
    created_at: datetime


# ---- Locations ----
class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    address: str
