from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class ForecastResponse(BaseModel):
    date: date
    sku_id: str
    store: str
    forecast_demand: int
    baseline_forecast: int

    class Config:
        from_attributes = True


class InventoryPolicyResponse(BaseModel):
    sku_id: str
    sku_name: str
    category: str
    store: str
    eoq: float
    safety_stock: float
    reorder_point: float
    current_inventory: float
    stockout_probability: float
    needs_reorder: bool
    forecast_4w_demand: int
    abc_class: Optional[str]
    xyz_class: Optional[str]
    segment: Optional[str]
    annual_revenue: float
    price: float
    lead_time_days: int

    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    sku_id: str
    store: str
    model: str
    mape: float
    smape: float
    rmse: float
    bias: float
    cv_smape: Optional[float]
    baseline_smape: Optional[float]
    improvement_vs_baseline: Optional[float]

    class Config:
        from_attributes = True


class WhatIfRequest(BaseModel):
    sku_id: str
    store: str
    demand_shock_pct: float = 0.0
    service_level: float = 0.95
    ordering_cost: float = 50.0
    holding_cost_rate: float = 0.25


class WhatIfResponse(BaseModel):
    eoq: float
    safety_stock: float
    reorder_point: float
    stockout_probability: float
    adjusted_demand: float
    original_eoq: float
    original_safety_stock: float
    original_reorder_point: float
    original_stockout_probability: float


class SummaryStats(BaseModel):
    total_skus: int
    total_stores: int
    reorder_alerts: int
    avg_mape: float
    high_risk_items: int
    total_annual_revenue: float
