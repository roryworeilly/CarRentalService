"""Auth service: register (F.R 1.1, 21+ & licence) and login (F.R 1.2)."""
from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User, DriverLicence
from ..schemas import RegisterIn, LoginIn
from ..security import hash_password, verify_password


def _age(dob: date, on=None) -> int:
    on = on or date.today()
    years = on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))
    return years


def register(db: Session, data: RegisterIn) -> User:
    # F.R 1.1 — must be 21+ at registration.
    if _age(data.date_of_birth) < 21:
        raise HTTPException(status_code=400, detail="must be 21 or older")
    # F.R 1.1 — valid (unexpired) licence required.
    if data.licence.expires_on < date.today():
        raise HTTPException(status_code=400, detail="driver licence expired")

    exists = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role="CUSTOMER",
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        phone=data.phone,
    )
    db.add(user)
    db.flush()
    db.add(DriverLicence(
        user_id=user.id,
        number=data.licence.number,
        issuing_state=data.licence.issuing_state,
        expires_on=data.licence.expires_on,
    ))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, data: LoginIn) -> User:
    user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return user
