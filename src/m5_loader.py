"""
Walmart M5 Competition Dataset Loader
--------------------------------------
Downloads and processes the M5 dataset into the project's standard schema.

Required files in data/m5/:
  - sales_train_validation.csv
  - calendar.csv
  - sell_prices.csv

Download from: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
"""

import pandas as pd
import numpy as np
import os
import sys

M5_DIR = "data/m5"
OUT_PATH = "data/raw/sales_data.csv"

# 3 stores — one per state for geographic diversity
SELECTED_STORES = ["CA_1", "TX_1", "WI_1"]

# Number of top-selling items to keep (keeps pipeline fast, matches our 8-SKU setup)
N_ITEMS = 8

# Lead time by category (realistic retail assumptions)
LEAD_TIME_MAP = {
    "FOODS":     3,
    "HOUSEHOLD": 5,
    "HOBBIES":   7,
}


def check_files():
    required = ["sales_train_validation.csv", "calendar.csv", "sell_prices.csv"]
    missing = [f for f in required if not os.path.exists(os.path.join(M5_DIR, f))]
    if missing:
        print("\nMissing M5 files:")
        for f in missing:
            print(f"  data/m5/{f}")
        print("\nDownload steps:")
        print("  1. Go to: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data")
        print("  2. Sign in to Kaggle and accept competition rules")
        print("  3. Download these 3 files:")
        print("       sales_train_validation.csv")
        print("       calendar.csv")
        print("       sell_prices.csv")
        print(f"  4. Place them in: {os.path.abspath(M5_DIR)}")
        print("  5. Run this script again\n")
        sys.exit(1)


def load_m5():
    check_files()

    print("[1/5] Loading calendar...")
    calendar = pd.read_csv(f"{M5_DIR}/calendar.csv", parse_dates=["date"])
    # d column is like "d_1", "d_2" etc — extract the number
    calendar["d_num"] = calendar["d"].str.replace("d_", "").astype(int)

    print("[2/5] Loading sell prices...")
    prices = pd.read_csv(f"{M5_DIR}/sell_prices.csv")

    print("[3/5] Loading sales data (large file — may take ~30 seconds)...")
    sales = pd.read_csv(f"{M5_DIR}/sales_train_validation.csv")

    # Filter to selected stores first to reduce memory
    sales = sales[sales["store_id"].isin(SELECTED_STORES)].copy()

    # Select top items spread across categories (FOODS, HOUSEHOLD, HOBBIES)
    # so the dashboard shows category diversity — not just all FOODS
    day_cols = [c for c in sales.columns if c.startswith("d_")]
    sales["_total"] = sales[day_cols].sum(axis=1)

    per_cat = {"FOODS": 3, "HOUSEHOLD": 3, "HOBBIES": 2}
    top_items = []
    for cat, n in per_cat.items():
        cat_sales = sales[sales["cat_id"] == cat]
        if len(cat_sales) == 0:
            continue
        items = (
            cat_sales.groupby("item_id")["_total"]
            .sum()
            .nlargest(n)
            .index.tolist()
        )
        top_items.extend(items)

    # Fallback: if any category missing, fill from overall top items
    if len(top_items) < N_ITEMS:
        extras = (
            sales[~sales["item_id"].isin(top_items)]
            .groupby("item_id")["_total"]
            .sum()
            .nlargest(N_ITEMS - len(top_items))
            .index.tolist()
        )
        top_items.extend(extras)

    sales = sales[sales["item_id"].isin(top_items)].drop(columns=["_total"])
    print(f"      Selected {len(top_items)} items across categories: {top_items}")

    print("[4/5] Transforming to long format...")
    id_cols = ["item_id", "dept_id", "cat_id", "store_id", "state_id"]
    sales_long = sales.melt(
        id_vars=id_cols,
        value_vars=day_cols,
        var_name="d",
        value_name="demand",
    )
    sales_long["d_num"] = sales_long["d"].str.replace("d_", "").astype(int)

    # Join calendar
    cal_cols = ["d_num", "date", "wm_yr_wk", "weekday",
                "event_name_1", "snap_CA", "snap_TX", "snap_WI"]
    sales_long = sales_long.merge(calendar[cal_cols], on="d_num", how="left")

    # Join prices (weekly price per store-item)
    sales_long = sales_long.merge(
        prices[["store_id", "item_id", "wm_yr_wk", "sell_price"]],
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
    )

    # Fill missing prices with item median
    sales_long["sell_price"] = sales_long.groupby("item_id")["sell_price"].transform(
        lambda x: x.fillna(x.median())
    )

    print("[5/5] Building features and saving...")

    # Event flags
    sales_long["is_holiday"] = sales_long["event_name_1"].notna().astype(int)
    sales_long["is_weekend"]  = sales_long["weekday"].isin(["Saturday", "Sunday"]).astype(int)

    # SNAP days = promotional / high-demand days per state
    sales_long["is_promo"] = 0
    for state, col in [("CA", "snap_CA"), ("TX", "snap_TX"), ("WI", "snap_WI")]:
        mask = sales_long["state_id"] == state
        sales_long.loc[mask, "is_promo"] = sales_long.loc[mask, col].astype(int)

    # Lead times by category
    sales_long["lead_time_days"] = sales_long["cat_id"].map(LEAD_TIME_MAP).fillna(5).astype(int)

    # Rename to match project schema
    result = sales_long.rename(columns={
        "item_id":    "sku_id",
        "dept_id":    "sku_name",
        "cat_id":     "category",
        "store_id":   "store",
        "sell_price": "price",
    })

    final_cols = [
        "date", "sku_id", "sku_name", "category", "store",
        "demand", "price", "is_holiday", "is_weekend", "is_promo", "lead_time_days",
    ]
    result = (
        result[final_cols]
        .dropna(subset=["price"])
        .sort_values(["sku_id", "store", "date"])
        .reset_index(drop=True)
    )

    os.makedirs("data/raw", exist_ok=True)
    result.to_csv(OUT_PATH, index=False)

    print(f"\nM5 dataset ready:")
    print(f"  Rows       : {len(result):,}")
    print(f"  SKUs       : {result['sku_id'].nunique()} -> {result['sku_id'].unique().tolist()}")
    print(f"  Stores     : {result['store'].nunique()} -> {result['store'].unique().tolist()}")
    print(f"  Date range : {result['date'].min().date()} to {result['date'].max().date()}")
    print(f"  Categories : {result['category'].unique().tolist()}")
    print(f"  Saved to   : {OUT_PATH}")

    return result


if __name__ == "__main__":
    load_m5()
