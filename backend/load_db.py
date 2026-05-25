"""
Load pipeline CSV outputs into PostgreSQL.
Run after: python src/run_pipeline.py
"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base, SessionLocal
from models import SalesData, Forecast, InventoryPolicy, ModelMetrics

BASE = os.path.join(os.path.dirname(__file__), "..")


def load_table(model_cls, df, rename_map=None):
    db = SessionLocal()
    db.query(model_cls).delete()
    db.commit()
    if rename_map:
        df = df.rename(columns=rename_map)
    cols = [c.name for c in model_cls.__table__.columns if c.name != "id"]
    df = df[[c for c in cols if c in df.columns]]
    records = df.to_dict(orient="records")
    db.bulk_insert_mappings(model_cls, records)
    db.commit()
    db.close()
    print(f"  Loaded {len(records):,} rows -> {model_cls.__tablename__}")


def main():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Loading sales data...")
    sales = pd.read_csv(os.path.join(BASE, "data/raw/sales_data.csv"), parse_dates=["date"])
    sales["date"] = sales["date"].dt.date
    load_table(SalesData, sales)

    print("Loading forecasts...")
    forecasts = pd.read_csv(os.path.join(BASE, "data/processed/forecasts.csv"), parse_dates=["date"])
    forecasts["date"] = forecasts["date"].dt.date
    load_table(Forecast, forecasts)

    print("Loading inventory policy...")
    inv = pd.read_csv(os.path.join(BASE, "data/processed/inventory_policy.csv"))
    load_table(InventoryPolicy, inv)

    print("Loading model metrics...")
    met = pd.read_csv(os.path.join(BASE, "models/saved/model_metrics.csv"))
    rename = {
        "MAPE": "mape", "SMAPE": "smape", "RMSE": "rmse",
        "Bias": "bias", "model": "model",
    }
    load_table(ModelMetrics, met, rename_map=rename)

    print("\nAll data loaded into PostgreSQL successfully.")


if __name__ == "__main__":
    main()
