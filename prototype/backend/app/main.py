"""FastAPI app entrypoint. CORS, routers, global exception handlers.

Postgres `EXCLUDE USING gist` enforces no-double-booking at the DB; violations
surface as IntegrityError with SQLSTATE 23P01 — mapped to HTTP 409.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .auth.router import router as auth_router
from .booking.router import router as booking_router
from .catalog.router import router as catalog_router

app = FastAPI(title="Car Rental Service — Prototype API", version="0.1.0")

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
    sqlstate = getattr(getattr(exc.orig, "pgcode", None), "__str__", lambda: "")()
    # psycopg2 exposes pgcode as a str attribute on the orig exception
    code = getattr(exc.orig, "pgcode", None)
    if code == "23P01" or sqlstate == "23P01":
        return JSONResponse(status_code=409, content={"detail": "vehicle already booked for that period"})
    if code == "23505" or sqlstate == "23505":
        return JSONResponse(status_code=409, content={"detail": "duplicate key"})
    return JSONResponse(status_code=400, content={"detail": "database integrity error"})


@app.get("/health")
def health():
    return {"status": "ok"}
