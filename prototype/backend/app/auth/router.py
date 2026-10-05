"""Auth router: POST /auth/register, POST /auth/login."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import RegisterIn, LoginIn, TokenOut
from ..security import create_access_token
from . import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = service.register(db, body)
    token = create_access_token(subject=user.id, role=user.role)
    return TokenOut(access_token=token, role=user.role, user_id=user.id)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = service.authenticate(db, body)
    token = create_access_token(subject=user.id, role=user.role)
    return TokenOut(access_token=token, role=user.role, user_id=user.id)
