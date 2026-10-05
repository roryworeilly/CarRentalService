"""Catalog router: GET /vehicles. F.R 2.1-2.4."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import VehicleSearchOut
from . import service

router = APIRouter(prefix="/vehicles", tags=["catalog"])


@router.get("", response_model=list[VehicleSearchOut])
def list_vehicles(
    category: Optional[str] = Query(None, description="VehicleCategory.name"),
    location_id: Optional[int] = Query(None),
    period_start: Optional[datetime] = Query(None),
    period_end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return service.search_vehicles(
        db,
        category=category,
        location_id=location_id,
        period_start=period_start,
        period_end=period_end,
    )


@router.get("/{vehicle_id}", response_model=VehicleSearchOut)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = service.get_vehicle(db, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle
