"""
Master pipeline runner.

Usage:
  python src/run_pipeline.py          # uses synthetic data (default)
  python src/run_pipeline.py --m5     # uses Walmart M5 real data
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def main():
    use_m5 = "--m5" in sys.argv

    print("=" * 60)
    print("  AI Demand Forecasting & Inventory Optimization Pipeline")
    print(f"  Data source: {'Walmart M5 (real)' if use_m5 else 'Synthetic'}")
    print("=" * 60)

    if use_m5:
        print("\n[1/4] Loading Walmart M5 dataset...")
        from m5_loader import load_m5
        load_m5()
    else:
        print("\n[1/4] Generating synthetic retail dataset...")
        from generate_data import generate_dataset
        generate_dataset()

    print("\n[2/4] Running data pipeline & feature engineering...")
    from data_pipeline import preprocess
    preprocess()

    print("\n[3/4] Training XGBoost forecasting models...")
    from forecasting import run_forecasting_pipeline
    metrics_df, forecasts = run_forecasting_pipeline()

    print("\n[4/4] Running inventory optimization...")
    from inventory_optimization import run_inventory_optimization
    inventory_df, alerts, segments = run_inventory_optimization()

    print("\n" + "=" * 60)
    print("Pipeline complete. Summary:")
    print(f"  Avg forecast MAPE : {metrics_df['MAPE'].mean():.2f}%")
    print(f"  Reorder alerts    : {len(alerts)} SKU-Store pairs")
    print(f"  High-risk items   : {(inventory_df['stockout_probability'] > 0.3).sum()}")
    print("\nOutputs:")
    print("  data/processed/features.csv")
    print("  data/processed/forecasts.csv")
    print("  data/processed/inventory_policy.csv")
    print("  data/processed/reorder_alerts.csv")
    print("  models/saved/model_metrics.csv")
    print("\nNext:")
    print("  1. cd backend && python load_db.py        (reload PostgreSQL)")
    print("  2. cd backend && uvicorn main:app --reload (API on :8000)")
    print("  3. cd frontend && npm run dev              (React on :5173)")
    print("=" * 60)


if __name__ == "__main__":
    main()
