from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime
from sqlalchemy.sql import func
from database import Base


class SalesData(Base):
    __tablename__ = "sales_data"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    sku_id = Column(String, index=True)
    sku_name = Column(String)
    category = Column(String)
    store = Column(String, index=True)
    demand = Column(Integer)
    price = Column(Float)
    is_holiday = Column(Boolean)
    is_weekend = Column(Boolean)
    is_promo = Column(Boolean)
    lead_time_days = Column(Integer)


class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    sku_id = Column(String, index=True)
    store = Column(String, index=True)
    forecast_demand = Column(Integer)
    baseline_forecast = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryPolicy(Base):
    __tablename__ = "inventory_policy"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String, index=True)
    sku_name = Column(String)
    category = Column(String)
    store = Column(String, index=True)
    eoq = Column(Float)
    safety_stock = Column(Float)
    reorder_point = Column(Float)
    current_inventory = Column(Float)
    stockout_probability = Column(Float)
    needs_reorder = Column(Boolean)
    forecast_4w_demand = Column(Integer)
    abc_class = Column(String)
    xyz_class = Column(String)
    segment = Column(String)
    annual_revenue = Column(Float)
    demand_mean = Column(Float)
    demand_std = Column(Float)
    price = Column(Float)
    lead_time_days = Column(Integer)


class ModelMetrics(Base):
    __tablename__ = "model_metrics"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String, index=True)
    store = Column(String)
    model = Column(String)
    mape = Column(Float)
    smape = Column(Float)
    rmse = Column(Float)
    bias = Column(Float)
    cv_smape = Column(Float)
    baseline_smape = Column(Float)
    improvement_vs_baseline = Column(Float)
