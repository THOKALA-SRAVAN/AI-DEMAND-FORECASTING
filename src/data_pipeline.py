import pandas as pd
import numpy as np
import os


def load_raw_data(path="data/raw/sales_data.csv"):
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def add_time_features(df):
    df = df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["dayofweek"] = df["date"].dt.dayofweek
    df["dayofyear"] = df["date"].dt.dayofyear
    df["quarter"] = df["date"].dt.quarter
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    return df


def add_lag_features(df, lags=[7, 14, 21, 28]):
    df = df.sort_values(["sku_id", "store", "date"]).copy()
    for lag in lags:
        df[f"lag_{lag}"] = df.groupby(["sku_id", "store"])["demand"].shift(lag)
    return df


def add_rolling_features(df, windows=[7, 14, 30]):
    df = df.sort_values(["sku_id", "store", "date"]).copy()
    for w in windows:
        grp = df.groupby(["sku_id", "store"])["demand"]
        df[f"rolling_mean_{w}"] = grp.shift(1).transform(lambda x: x.rolling(w, min_periods=1).mean())
        df[f"rolling_std_{w}"] = grp.shift(1).transform(lambda x: x.rolling(w, min_periods=1).std())
        df[f"rolling_max_{w}"] = grp.shift(1).transform(lambda x: x.rolling(w, min_periods=1).max())
    return df


def aggregate_weekly(df):
    weekly = (
        df.groupby(["sku_id", "sku_name", "category", "store",
                    pd.Grouper(key="date", freq="W-MON")])
        .agg(
            demand=("demand", "sum"),
            price=("price", "first"),
            lead_time_days=("lead_time_days", "first"),
            is_holiday=("is_holiday", "max"),
            is_promo=("is_promo", "max"),
        )
        .reset_index()
    )
    return weekly


def preprocess(path="data/raw/sales_data.csv"):
    df = load_raw_data(path)
    df = add_time_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df)
    df = df.dropna()

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/features.csv", index=False)

    weekly = aggregate_weekly(load_raw_data(path))
    weekly.to_csv("data/processed/weekly_sales.csv", index=False)

    print(f"Processed: {len(df):,} rows with features")
    print(f"Weekly aggregated: {len(weekly):,} rows")
    return df, weekly


if __name__ == "__main__":
    preprocess()
