import pandas as pd
import numpy as np
import warnings
import os
import pickle
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error

warnings.filterwarnings("ignore")


# ── Metrics ────────────────────────────────────────────────────────────────────

def smape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    denom = np.where(denom == 0, 1, denom)
    return float(np.mean(np.abs(y_true - y_pred) / denom) * 100)


def evaluate(y_true, y_pred, model_name="Model"):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # MAPE is undefined when actual=0 (common in M5 intermittent demand data)
    # Only compute on non-zero actuals to avoid infinity
    nonzero = y_true > 0
    if nonzero.sum() > 0:
        mape = float(mean_absolute_percentage_error(y_true[nonzero], y_pred[nonzero]) * 100)
    else:
        mape = 0.0
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    bias = float(np.mean(np.array(y_pred) - np.array(y_true)))
    s = smape(y_true, y_pred)
    return {
        "model": model_name,
        "MAPE": round(mape, 2),
        "SMAPE": round(s, 2),
        "RMSE": round(rmse, 2),
        "Bias": round(bias, 2),
    }


# ── Walk-forward cross-validation ─────────────────────────────────────────────

def walk_forward_cv(df, model_fn, n_splits=3, test_size=4):
    """
    Time-series walk-forward validation — never leaks future data into training.
    Each fold trains only on past data and tests on unseen future weeks.
    """
    scores = []
    n = len(df)
    for i in range(n_splits):
        train_end = n - (n_splits - i) * test_size
        if train_end < 20:
            continue
        train = df.iloc[:train_end]
        test = df.iloc[train_end: train_end + test_size]
        if len(test) == 0:
            continue
        preds = model_fn(train, test)
        preds = np.maximum(0, preds)
        scores.append(smape(test["demand"].values, preds))
    return round(float(np.mean(scores)), 2) if scores else None


# ── Feature columns ────────────────────────────────────────────────────────────

FEATURE_COLS = [
    "week", "month", "quarter", "dayofyear",
    "month_sin", "month_cos", "dow_sin", "dow_cos",
    "lag_7", "lag_14", "lag_21", "lag_28",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_30",
    "rolling_std_7", "rolling_std_14",
    "is_holiday", "is_weekend", "is_promo",
]


# ── Baseline: 4-week rolling average ──────────────────────────────────────────

def baseline_forecast(train_df, test_df):
    avg = train_df["demand"].tail(4).mean()
    return np.full(len(test_df), avg)


# ── XGBoost Model ─────────────────────────────────────────────────────────────

def xgb_predict(train_df, test_df):
    available = [c for c in FEATURE_COLS if c in train_df.columns and c in test_df.columns]
    X_train = train_df[available].fillna(0)
    y_train = train_df["demand"]
    X_test = test_df[available].fillna(0)
    model = XGBRegressor(
        n_estimators=300, learning_rate=0.05,
        max_depth=5, subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_train, y_train)], verbose=False)
    return np.maximum(0, model.predict(X_test))


def train_xgb_model(subset_df):
    """Train full XGBoost model and return model + feature importance."""
    available = [c for c in FEATURE_COLS if c in subset_df.columns]
    subset = subset_df.dropna(subset=available).copy()
    if len(subset) < 30:
        return None, None, None

    subset = subset.sort_values("date")
    split = int(len(subset) * 0.8)
    train = subset.iloc[:split]
    test = subset.iloc[split:]

    model = XGBRegressor(
        n_estimators=300, learning_rate=0.05,
        max_depth=5, subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbosity=0,
    )
    model.fit(train[available], train["demand"], verbose=False)
    preds = np.maximum(0, model.predict(test[available]))
    metrics = evaluate(test["demand"].values, preds, "XGBoost")

    importance = dict(zip(available, model.feature_importances_))
    return model, metrics, importance


# ── Future feature generation ──────────────────────────────────────────────────

def build_future_features(history_df, n_weeks):
    """Generate feature rows for future forecast periods using rolling history."""
    last_date = history_df["date"].max()
    future_dates = pd.date_range(
        last_date + pd.Timedelta(weeks=1), periods=n_weeks, freq="W-MON"
    )
    rows = []
    for fd in future_dates:
        row = {
            "date": fd,
            "week": fd.isocalendar().week,
            "month": fd.month,
            "quarter": fd.quarter,
            "dayofyear": fd.timetuple().tm_yday,
            "month_sin": np.sin(2 * np.pi * fd.month / 12),
            "month_cos": np.cos(2 * np.pi * fd.month / 12),
            "dow_sin": np.sin(2 * np.pi * fd.weekday() / 7),
            "dow_cos": np.cos(2 * np.pi * fd.weekday() / 7),
            "is_holiday": 0,
            "is_weekend": int(fd.weekday() >= 5),
            "is_promo": 0,
            "lag_7": history_df["demand"].iloc[-1] if len(history_df) >= 1 else 0,
            "lag_14": history_df["demand"].iloc[-2] if len(history_df) >= 2 else 0,
            "lag_21": history_df["demand"].iloc[-3] if len(history_df) >= 3 else 0,
            "lag_28": history_df["demand"].iloc[-4] if len(history_df) >= 4 else 0,
            "rolling_mean_7": history_df["demand"].tail(7).mean(),
            "rolling_mean_14": history_df["demand"].tail(14).mean(),
            "rolling_mean_30": history_df["demand"].tail(30).mean(),
            "rolling_std_7": history_df["demand"].tail(7).std(),
            "rolling_std_14": history_df["demand"].tail(14).std(),
        }
        rows.append(row)
    return pd.DataFrame(rows)


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_forecasting_pipeline(
    features_path="data/processed/features.csv",
    weekly_path="data/processed/weekly_sales.csv",
    forecast_weeks=8,
):
    print("Loading data...")
    weekly = pd.read_csv(weekly_path, parse_dates=["date"])
    features = pd.read_csv(features_path, parse_dates=["date"])

    all_metrics = []
    all_forecasts = []
    os.makedirs("models/saved", exist_ok=True)

    for sku in weekly["sku_id"].unique():
        for store in weekly["store"].unique():
            key = f"{sku}_{store}"
            subset = features[
                (features["sku_id"] == sku) & (features["store"] == store)
            ].sort_values("date").copy()

            weekly_sub = weekly[
                (weekly["sku_id"] == sku) & (weekly["store"] == store)
            ].sort_values("date")

            if len(subset) < 40:
                continue

            # Walk-forward CV with XGBoost
            cv_smape = walk_forward_cv(subset, xgb_predict)
            cv_baseline = walk_forward_cv(subset, baseline_forecast)

            # Train final model on all data except last forecast_weeks
            train_cut = subset.iloc[:-forecast_weeks] if len(subset) > forecast_weeks else subset
            model, metrics, importance = train_xgb_model(train_cut)

            if model is None:
                continue

            metrics["sku_id"] = sku
            metrics["store"] = store
            metrics["cv_smape"] = cv_smape
            metrics["baseline_smape"] = cv_baseline
            metrics["improvement_vs_baseline"] = (
                round(cv_baseline - cv_smape, 2) if cv_smape and cv_baseline else None
            )
            all_metrics.append(metrics)

            # Future forecast
            future_features = build_future_features(weekly_sub, forecast_weeks)
            available = [c for c in FEATURE_COLS if c in future_features.columns]
            future_preds = np.maximum(0, model.predict(future_features[available].fillna(0)))

            # Baseline (rolling avg) for comparison
            baseline_preds = np.full(forecast_weeks, weekly_sub["demand"].tail(4).mean())

            forecast_df = pd.DataFrame({
                "date": future_features["date"],
                "sku_id": sku,
                "store": store,
                "forecast_demand": future_preds.astype(int),
                "baseline_forecast": baseline_preds.astype(int),
            })
            all_forecasts.append(forecast_df)

            # Save model
            with open(f"models/saved/xgb_{key}.pkl", "wb") as f:
                pickle.dump(model, f)

            print(f"  {key}: MAPE={metrics['MAPE']}% | CV-SMAPE={cv_smape}% | vs baseline={cv_baseline}%")

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv("models/saved/model_metrics.csv", index=False)

    forecast_combined = pd.concat(all_forecasts, ignore_index=True)
    forecast_combined.to_csv("data/processed/forecasts.csv", index=False)

    print(f"\nAvg XGBoost MAPE : {metrics_df['MAPE'].mean():.2f}%")
    print(f"Avg CV SMAPE     : {metrics_df['cv_smape'].mean():.2f}%")
    print(f"Avg vs Baseline  : {metrics_df['improvement_vs_baseline'].mean():.2f}% better")
    return metrics_df, forecast_combined


if __name__ == "__main__":
    run_forecasting_pipeline()
