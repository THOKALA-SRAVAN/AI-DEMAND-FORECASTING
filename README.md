# AI Demand Forecasting & Inventory Optimization

End-to-end ML system for retail demand forecasting and inventory policy optimization.  
Built with **XGBoost**, **FastAPI**, **PostgreSQL**, and **React**.

## Architecture

```
src/              ← ML pipeline (data gen → features → XGBoost → inventory engine)
backend/          ← FastAPI REST API + PostgreSQL models
frontend/         ← React + Vite + Tailwind + Recharts dashboard
data/             ← Raw & processed CSVs
models/saved/     ← Trained XGBoost models (.pkl) + metrics
```

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| ML          | XGBoost, Scikit-learn, SciPy        |
| Backend API | FastAPI, SQLAlchemy, PostgreSQL      |
| Frontend    | React 18, Vite, Tailwind CSS, Recharts |
| Validation  | Walk-forward cross-validation (no data leakage) |

## Key Features

- **XGBoost demand forecasting** with lag features, rolling stats, and calendar features
- **Walk-forward cross-validation** — proper time-series evaluation, no future leakage
- **Economic Order Quantity (EOQ)** — minimizes total ordering + holding cost
- **Safety stock** computed from forecast uncertainty and lead time
- **Reorder point alerts** with stockout probability per SKU-Store
- **ABC-XYZ segmentation** — classify SKUs by revenue and demand variability
- **What-If simulator** — model the impact of demand shocks in real time
- **REST API** with auto-generated Swagger docs at `/docs`

## Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL running locally

### 2. Setup

```bash
# Python environment
pip install -r requirements.txt

# Copy and fill in your DB credentials
cp .env.example .env

# Create the database
psql -U postgres -c "CREATE DATABASE inventory_db;"
```

### 3. Run the ML pipeline

```bash
python src/run_pipeline.py
```

This generates ~200K rows of synthetic retail sales data, trains XGBoost models for
every SKU × Store combination, computes inventory policies, and saves results to CSV.

### 4. Load data into PostgreSQL

```bash
cd backend
python load_db.py
```

### 5. Start the API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: http://localhost:5173

## API Endpoints

| Method | Endpoint                   | Description                        |
|--------|----------------------------|------------------------------------|
| GET    | `/forecasts/`              | Get demand forecasts (filter by SKU/store) |
| GET    | `/forecasts/history`       | Historical sales for a SKU-Store   |
| GET    | `/forecasts/weekly-trend`  | Aggregated weekly sales trend      |
| GET    | `/inventory/`              | Inventory policy (EOQ, safety stock, etc.) |
| GET    | `/inventory/alerts`        | SKUs needing immediate reorder     |
| GET    | `/inventory/segments`      | ABC-XYZ segment summary            |
| POST   | `/inventory/whatif`        | What-if demand simulation          |
| GET    | `/metrics/summary`         | Dashboard summary stats            |
| GET    | `/metrics/`                | All model performance metrics      |

## Model Performance

XGBoost models are trained per SKU-Store pair using:
- **Lag features**: 7, 14, 21, 28-day lags
- **Rolling features**: 7/14/30-day rolling mean, std, max
- **Calendar features**: week, month, quarter, sin/cos encodings
- **Event features**: holiday, weekend, promotion flags

Evaluated using **walk-forward cross-validation** (3 folds) to prevent data leakage.  
Typical MAPE: **8–15%** depending on SKU volatility.

## Inventory Optimization

| Metric         | Formula                                                   |
|----------------|-----------------------------------------------------------|
| EOQ            | √(2 × D × S / H) — Wilson formula                       |
| Safety Stock   | Z × σ_d × √(lead time)                                  |
| Reorder Point  | avg_demand × lead_time + safety_stock                    |
| Stockout Prob  | 1 - Φ((inventory - μ_lt) / σ_lt)                        |

## Dashboard Pages

1. **Overview** — KPIs, sales trend, revenue by category
2. **Demand Forecast** — Per-SKU forecast vs. actuals + model metrics
3. **Inventory Policy** — Full EOQ/safety stock table with filters
4. **Reorder Alerts** — Prioritized stockout risk alerts
5. **ABC-XYZ Segmentation** — Revenue × variability scatter + segment table
6. **Model Performance** — MAPE distribution, RMSE scatter, full metrics table
7. **What-If Simulator** — Interactive demand shock and cost parameter exploration
