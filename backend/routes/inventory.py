from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import numpy as np
from scipy import stats
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.database import get_db
from backend.models import InventoryPolicy
from backend.schemas import InventoryPolicyResponse, WhatIfRequest, WhatIfResponse

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=List[InventoryPolicyResponse])
def get_inventory(
    store: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    abc_class: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(InventoryPolicy)
    if store:
        q = q.filter(InventoryPolicy.store == store)
    if category:
        q = q.filter(InventoryPolicy.category == category)
    if abc_class:
        q = q.filter(InventoryPolicy.abc_class == abc_class)
    return q.all()


@router.get("/alerts", response_model=List[InventoryPolicyResponse])
def get_reorder_alerts(db: Session = Depends(get_db)):
    return (
        db.query(InventoryPolicy)
        .filter(InventoryPolicy.needs_reorder == True)
        .order_by(InventoryPolicy.stockout_probability.desc())
        .all()
    )


@router.get("/segments")
def get_segments(db: Session = Depends(get_db)):
    rows = db.query(InventoryPolicy).all()
    segment_map = {}
    for r in rows:
        seg = r.segment or "Unknown"
        if seg not in segment_map:
            segment_map[seg] = {"count": 0, "revenue": 0.0, "abc": r.abc_class, "xyz": r.xyz_class}
        segment_map[seg]["count"] += 1
        segment_map[seg]["revenue"] += r.annual_revenue or 0
    return [{"segment": k, **v} for k, v in segment_map.items()]


@router.get("/category-revenue")
def get_category_revenue(db: Session = Depends(get_db)):
    rows = db.query(InventoryPolicy).all()
    cat_map = {}
    for r in rows:
        cat = r.category
        cat_map[cat] = cat_map.get(cat, 0) + (r.annual_revenue or 0)
    return [{"category": k, "annual_revenue": round(v, 2)} for k, v in cat_map.items()]


@router.post("/whatif", response_model=WhatIfResponse)
def what_if_simulation(req: WhatIfRequest, db: Session = Depends(get_db)):
    row = (
        db.query(InventoryPolicy)
        .filter(InventoryPolicy.sku_id == req.sku_id, InventoryPolicy.store == req.store)
        .first()
    )
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SKU/Store combination not found")

    # Adjusted demand
    adj_demand = row.demand_mean * (1 + req.demand_shock_pct / 100)
    adj_std = row.demand_std * (1 + abs(req.demand_shock_pct) / 200)
    annual_demand = adj_demand * 52
    holding_cost = row.price * req.holding_cost_rate

    # EOQ
    new_eoq = float(np.sqrt((2 * annual_demand * req.ordering_cost) / max(holding_cost, 0.01)))

    # Safety stock
    z = float(stats.norm.ppf(req.service_level))
    lt_weeks = row.lead_time_days / 7
    new_ss = z * adj_std * float(np.sqrt(lt_weeks))

    # Reorder point
    new_rop = adj_demand * lt_weeks + new_ss

    # Stockout probability
    expected = adj_demand * lt_weeks
    std_lt = adj_std * float(np.sqrt(lt_weeks))
    if std_lt > 0:
        new_stockout = float(1 - stats.norm.cdf(row.current_inventory, loc=expected, scale=std_lt))
        new_stockout = float(np.clip(new_stockout, 0, 1))
    else:
        new_stockout = 0.0

    return WhatIfResponse(
        eoq=round(new_eoq, 1),
        safety_stock=round(new_ss, 1),
        reorder_point=round(new_rop, 1),
        stockout_probability=round(new_stockout, 4),
        adjusted_demand=round(adj_demand, 2),
        original_eoq=round(row.eoq, 1),
        original_safety_stock=round(row.safety_stock, 1),
        original_reorder_point=round(row.reorder_point, 1),
        original_stockout_probability=round(row.stockout_probability, 4),
    )
