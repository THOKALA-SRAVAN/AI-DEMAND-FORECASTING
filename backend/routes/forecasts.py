from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import get_db
from backend.models import Forecast, SalesData
from backend.schemas import ForecastResponse

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get("/", response_model=List[ForecastResponse])
def get_forecasts(
    sku_id: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Forecast)
    if sku_id:
        q = q.filter(Forecast.sku_id == sku_id)
    if store:
        q = q.filter(Forecast.store == store)
    return q.order_by(Forecast.date).all()


@router.get("/skus")
def get_skus(db: Session = Depends(get_db)):
    skus = db.query(Forecast.sku_id).distinct().all()
    return [s[0] for s in skus]


@router.get("/stores")
def get_stores(db: Session = Depends(get_db)):
    stores = db.query(Forecast.store).distinct().all()
    return [s[0] for s in stores]


@router.get("/history")
def get_history(
    sku_id: str = Query(...),
    store: str = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(SalesData)
        .filter(SalesData.sku_id == sku_id, SalesData.store == store)
        .order_by(SalesData.date)
        .all()
    )
    return [{"date": str(r.date), "demand": r.demand} for r in rows]


@router.get("/weekly-trend")
def get_weekly_trend(db: Session = Depends(get_db)):
    rows = (
        db.query(SalesData.date, func.sum(SalesData.demand).label("total_demand"))
        .group_by(SalesData.date)
        .order_by(SalesData.date)
        .all()
    )
    return [{"date": str(r.date), "demand": r.total_demand} for r in rows]
