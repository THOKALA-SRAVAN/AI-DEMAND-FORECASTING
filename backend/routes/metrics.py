from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import get_db
from backend.models import ModelMetrics, InventoryPolicy
from backend.schemas import MetricsResponse, SummaryStats

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/", response_model=List[MetricsResponse])
def get_metrics(db: Session = Depends(get_db)):
    return db.query(ModelMetrics).all()


@router.get("/summary", response_model=SummaryStats)
def get_summary(db: Session = Depends(get_db)):
    inv = db.query(InventoryPolicy).all()
    met = db.query(ModelMetrics).all()

    total_skus = db.query(InventoryPolicy.sku_id).distinct().count()
    total_stores = db.query(InventoryPolicy.store).distinct().count()
    reorder_alerts = sum(1 for i in inv if i.needs_reorder)
    avg_mape = float(sum(m.mape for m in met) / len(met)) if met else 0.0
    high_risk = sum(1 for i in inv if i.stockout_probability and i.stockout_probability > 0.3)
    total_revenue = sum(i.annual_revenue for i in inv if i.annual_revenue) / 3  # per store avg

    return SummaryStats(
        total_skus=total_skus,
        total_stores=total_stores,
        reorder_alerts=reorder_alerts,
        avg_mape=round(avg_mape, 2),
        high_risk_items=high_risk,
        total_annual_revenue=round(total_revenue, 2),
    )


@router.get("/mape-by-sku")
def mape_by_sku(db: Session = Depends(get_db)):
    rows = db.query(ModelMetrics).all()
    sku_map = {}
    for r in rows:
        if r.sku_id not in sku_map:
            sku_map[r.sku_id] = []
        sku_map[r.sku_id].append(r.mape)
    return [{"sku_id": k, "avg_mape": round(sum(v) / len(v), 2)} for k, v in sku_map.items()]
