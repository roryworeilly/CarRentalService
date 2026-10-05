"""FastAPI app entrypoint. CORS, routers, global exception handlers.

Postgres `EXCLUDE USING gist` enforces no-double-booking at the DB; violations
surface as IntegrityError with SQLSTATE 23P01 — mapped to HTTP 409.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .auth.router import router as auth_router
from .booking.router import router as booking_router
from .booking.service import expire_stale_holds
from .catalog.router import router as catalog_router
from .db import SessionLocal


def _run_expiry():
    db = SessionLocal()
    try:
        expired = expire_stale_holds(db)
        if expired:
            print(f"[scheduler] expired {expired} stale hold(s)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_expiry, "interval", seconds=60)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Car Rental Service — Prototype API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prototype only — tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(booking_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError):
    """Translate the no-overlap EXCLUDE violation (SQLSTATE 23P01) → 409."""
    code = getattr(exc.orig, "pgcode", None)
    if code == "23P01":
        return JSONResponse(status_code=409, content={"detail": "vehicle already booked for that period"})
    if code == "23505":
        return JSONResponse(status_code=409, content={"detail": "duplicate key"})
    return JSONResponse(status_code=400, content={"detail": "database integrity error"})


@app.get("/health")
def health():
    return {"status": "ok"}
