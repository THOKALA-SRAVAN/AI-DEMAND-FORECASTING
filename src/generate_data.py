import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

SKUS = {
    "SKU_001": {"name": "Laptop",       "category": "Electronics", "base_demand": 50,  "price": 800, "lead_time": 7},
    "SKU_002": {"name": "Headphones",   "category": "Electronics", "base_demand": 120, "price": 150, "lead_time": 5},
    "SKU_003": {"name": "T-Shirt",      "category": "Apparel",     "base_demand": 300, "price": 25,  "lead_time": 3},
    "SKU_004": {"name": "Sneakers",     "category": "Apparel",     "base_demand": 180, "price": 90,  "lead_time": 4},
    "SKU_005": {"name": "Coffee Maker", "category": "Appliances",  "base_demand": 80,  "price": 120, "lead_time": 6},
    "SKU_006": {"name": "Desk Chair",   "category": "Furniture",   "base_demand": 40,  "price": 250, "lead_time": 10},
    "SKU_007": {"name": "Notebook",     "category": "Stationery",  "base_demand": 500, "price": 5,   "lead_time": 2},
    "SKU_008": {"name": "Water Bottle", "category": "Accessories", "base_demand": 220, "price": 30,  "lead_time": 3},
}

STORES = ["Store_A", "Store_B", "Store_C"]

HOLIDAYS = [
    "2022-01-01", "2022-11-25", "2022-12-25",
    "2023-01-01", "2023-11-24", "2023-12-25",
    "2024-01-01", "2024-11-29", "2024-12-25",
]


def generate_demand(base, n_days, sku_id):
    t = np.arange(n_days)
    trend = base * (1 + 0.0003 * t)
    weekly = base * 0.15 * np.sin(2 * np.pi * t / 7)
    annual = base * 0.25 * np.sin(2 * np.pi * t / 365 + np.pi * int(sku_id[-1]) / 4)
    noise = np.random.normal(0, base * 0.1, n_days)
    demand = np.maximum(0, trend + weekly + annual + noise).astype(int)
    return demand


def generate_dataset():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start_date, end_date, freq="D")
    n_days = len(dates)
    holiday_set = set(HOLIDAYS)

    records = []
    for sku_id, meta in SKUS.items():
        for store in STORES:
            demand = generate_demand(meta["base_demand"], n_days, sku_id)
            for i, date in enumerate(dates):
                is_holiday = str(date.date()) in holiday_set
                is_weekend = date.weekday() >= 5
                promo = np.random.random() < 0.05
                multiplier = 1.0
                if is_holiday:
                    multiplier *= 1.8
                if is_weekend:
                    multiplier *= 1.2
                if promo:
                    multiplier *= 1.5

                final_demand = int(demand[i] * multiplier)
                records.append({
                    "date": date,
                    "sku_id": sku_id,
                    "sku_name": meta["name"],
                    "category": meta["category"],
                    "store": store,
                    "demand": final_demand,
                    "price": meta["price"],
                    "is_holiday": is_holiday,
                    "is_weekend": is_weekend,
                    "is_promo": promo,
                    "lead_time_days": meta["lead_time"],
                })

    df = pd.DataFrame(records)
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv("data/raw/sales_data.csv", index=False)
    print(f"Dataset generated: {len(df):,} rows | {df['sku_id'].nunique()} SKUs | {df['store'].nunique()} stores")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    return df


if __name__ == "__main__":
    generate_dataset()
