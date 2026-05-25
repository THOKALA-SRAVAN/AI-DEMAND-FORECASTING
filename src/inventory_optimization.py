import pandas as pd
import numpy as np
from scipy import stats


# ── EOQ: Economic Order Quantity ──────────────────────────────────────────────

def calculate_eoq(annual_demand, ordering_cost, holding_cost_per_unit):
    """Wilson EOQ formula: minimizes total ordering + holding cost."""
    if holding_cost_per_unit <= 0 or annual_demand <= 0:
        return 0
    return np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)


# ── Safety Stock ──────────────────────────────────────────────────────────────

def calculate_safety_stock(demand_std, lead_time_days, service_level=0.95):
    """
    Safety stock based on forecast uncertainty and lead time.
    Uses normal distribution z-score for target service level.
    """
    z = stats.norm.ppf(service_level)
    lead_time_weeks = lead_time_days / 7
    return z * demand_std * np.sqrt(lead_time_weeks)


# ── Reorder Point ─────────────────────────────────────────────────────────────

def calculate_reorder_point(avg_weekly_demand, lead_time_days, safety_stock):
    """Reorder when inventory hits this level to avoid stockout during lead time."""
    lead_time_weeks = lead_time_days / 7
    return (avg_weekly_demand * lead_time_weeks) + safety_stock


# ── Stockout Probability ───────────────────────────────────────────────────────

def stockout_probability(current_inventory, avg_demand, demand_std, lead_time_days):
    """Probability that demand exceeds inventory during lead time."""
    lead_time_weeks = lead_time_days / 7
    expected_demand = avg_demand * lead_time_weeks
    demand_variance = (demand_std ** 2) * lead_time_weeks
    if demand_variance <= 0:
        return 0.0
    demand_during_lt_std = np.sqrt(demand_variance)
    prob = 1 - stats.norm.cdf(current_inventory, loc=expected_demand, scale=demand_during_lt_std)
    return round(float(np.clip(prob, 0, 1)), 4)


# ── ABC-XYZ Segmentation ──────────────────────────────────────────────────────

def abc_segmentation(df_sku_summary):
    """
    ABC: classify by revenue contribution.
    A = top 70%, B = next 20%, C = bottom 10%
    """
    df = df_sku_summary.copy().sort_values("annual_revenue", ascending=False)
    df["revenue_pct"] = df["annual_revenue"] / df["annual_revenue"].sum()
    df["cumulative_pct"] = df["revenue_pct"].cumsum()
    df["abc_class"] = "C"
    df.loc[df["cumulative_pct"] <= 0.70, "abc_class"] = "A"
    df.loc[(df["cumulative_pct"] > 0.70) & (df["cumulative_pct"] <= 0.90), "abc_class"] = "B"
    return df


def xyz_segmentation(df_sku_summary):
    """
    XYZ: classify by demand variability (CoV = std/mean).
    X = stable (CoV < 0.5), Y = variable (0.5-1.0), Z = highly variable (>1.0)
    """
    df = df_sku_summary.copy()
    df["cov"] = df["demand_std"] / df["demand_mean"].replace(0, np.nan)
    df["xyz_class"] = "Z"
    df.loc[df["cov"] < 0.5, "xyz_class"] = "X"
    df.loc[(df["cov"] >= 0.5) & (df["cov"] < 1.0), "xyz_class"] = "Y"
    return df


# ── Full Inventory Policy Engine ──────────────────────────────────────────────

def run_inventory_optimization(
    weekly_path="data/processed/weekly_sales.csv",
    forecast_path="data/processed/forecasts.csv",
    ordering_cost=50,
    holding_cost_rate=0.25,
    service_level=0.95,
):
    print("Running inventory optimization...")
    weekly = pd.read_csv(weekly_path, parse_dates=["date"])
    forecasts = pd.read_csv(forecast_path, parse_dates=["date"])

    sku_meta = weekly.groupby(["sku_id", "sku_name", "category", "store"]).agg(
        demand_mean=("demand", "mean"),
        demand_std=("demand", "std"),
        annual_demand=("demand", lambda x: x.sum() / (len(x) / 52)),
        price=("price", "first"),
        lead_time_days=("lead_time_days", "first"),
    ).reset_index()

    sku_meta["annual_revenue"] = sku_meta["annual_demand"] * sku_meta["price"]
    sku_meta["holding_cost_per_unit"] = sku_meta["price"] * holding_cost_rate

    results = []
    for _, row in sku_meta.iterrows():
        eoq = calculate_eoq(
            row["annual_demand"], ordering_cost, row["holding_cost_per_unit"]
        )
        safety_stock = calculate_safety_stock(
            row["demand_std"], row["lead_time_days"], service_level
        )
        reorder_point = calculate_reorder_point(
            row["demand_mean"], row["lead_time_days"], safety_stock
        )
        # Simulate varied inventory levels: some healthy, some at/below reorder point
        # Uses a seeded random so results are reproducible
        rng = np.random.default_rng(seed=abs(hash(f"{row['sku_id']}_{row['store']}")) % (2**32))
        inventory_weeks = rng.choice([0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0],
                                      p=[0.05, 0.10, 0.15, 0.15, 0.20, 0.20, 0.10, 0.05])
        current_inventory = row["demand_mean"] * inventory_weeks
        stockout_prob = stockout_probability(
            current_inventory, row["demand_mean"],
            row["demand_std"], row["lead_time_days"]
        )
        needs_reorder = current_inventory <= reorder_point

        # Next 4-week forecast demand
        key_forecast = forecasts[
            (forecasts["sku_id"] == row["sku_id"]) &
            (forecasts["store"] == row["store"])
        ]["forecast_demand"].head(4).sum()

        results.append({
            **row.to_dict(),
            "eoq": round(eoq, 0),
            "safety_stock": round(safety_stock, 0),
            "reorder_point": round(reorder_point, 0),
            "current_inventory": round(current_inventory, 0),
            "stockout_probability": stockout_prob,
            "needs_reorder": needs_reorder,
            "forecast_4w_demand": int(key_forecast),
            "service_level": service_level,
        })

    inventory_df = pd.DataFrame(results)

    # ABC-XYZ segmentation
    sku_level = inventory_df.groupby("sku_id").agg(
        annual_revenue=("annual_revenue", "sum"),
        demand_mean=("demand_mean", "mean"),
        demand_std=("demand_std", "mean"),
        sku_name=("sku_name", "first"),
        category=("category", "first"),
    ).reset_index()

    sku_level = abc_segmentation(sku_level)
    sku_level = xyz_segmentation(sku_level)
    sku_level["segment"] = sku_level["abc_class"] + sku_level["xyz_class"]

    inventory_df = inventory_df.merge(
        sku_level[["sku_id", "abc_class", "xyz_class", "segment", "cov"]],
        on="sku_id", how="left"
    )

    inventory_df.to_csv("data/processed/inventory_policy.csv", index=False)

    reorder_alerts = inventory_df[inventory_df["needs_reorder"]].copy()
    reorder_alerts = reorder_alerts.sort_values("stockout_probability", ascending=False)
    reorder_alerts.to_csv("data/processed/reorder_alerts.csv", index=False)

    print(f"Inventory policy computed for {len(inventory_df)} SKU-Store combinations")
    print(f"Reorder alerts: {len(reorder_alerts)} items need restocking")
    print(f"High-risk items (stockout > 30%): {(inventory_df['stockout_probability'] > 0.3).sum()}")

    return inventory_df, reorder_alerts, sku_level


if __name__ == "__main__":
    run_inventory_optimization()
