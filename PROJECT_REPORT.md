# AI Demand Forecasting & Inventory Optimization
## Project Report

**Project Title:** AI-Driven Demand Forecasting and Inventory Optimization System  
**Technology Stack:** XGBoost · FastAPI · PostgreSQL · React  
**Domain:** Retail Supply Chain · Machine Learning · Business Intelligence  

---

## 1. Abstract

This project presents an end-to-end machine learning system for retail demand forecasting and inventory policy optimization. The system ingests three years of synthetic retail sales data spanning 8 SKUs across 3 store locations, engineers time-series features, and trains XGBoost models per SKU-Store combination. Forecasts are evaluated using walk-forward cross-validation to prevent data leakage. The ML pipeline feeds an inventory optimization engine that computes Economic Order Quantity (EOQ), safety stock, reorder points, and stockout probabilities using statistical methods. Results are exposed through a FastAPI REST API backed by PostgreSQL and visualized via a React dashboard with 7 interactive pages. The system achieves an average forecast MAPE of 7.79% — a 10.65% improvement in SMAPE over the rolling average baseline — and identifies 8 SKU-Store combinations requiring immediate restocking with 4 flagged as high stockout risk.

---

## 2. Introduction & Problem Statement

Retail businesses lose an estimated $1.75 trillion globally each year due to inventory distortion — a combination of overstocking and stockouts. Traditional rule-of-thumb inventory management (fixed reorder quantities, manual stock checks) fails to account for demand seasonality, promotions, lead times, and forecast uncertainty.

This project addresses two interconnected problems:

**Problem 1 — Demand Forecasting:** Accurately predicting future product demand at the SKU-Store level, accounting for weekly seasonality, annual trends, promotional spikes, and holiday effects.

**Problem 2 — Inventory Optimization:** Translating demand forecasts and their uncertainty into actionable inventory policies — how much to order, when to order, and how much buffer stock to maintain to achieve a 95% service level without over-investing in inventory.

The solution is a unified system that moves from raw sales data → ML forecast → inventory policy → business action, all accessible through a web dashboard and REST API.

---

## 3. Objectives

1. Build a scalable, per-SKU demand forecasting pipeline using XGBoost with rich time-series features.
2. Implement proper walk-forward cross-validation to evaluate model accuracy without leaking future data into training.
3. Compute inventory optimization metrics (EOQ, safety stock, reorder point, stockout probability) directly from forecast outputs.
4. Classify SKUs using ABC-XYZ segmentation to prioritize inventory management effort.
5. Deploy a production-style REST API (FastAPI + PostgreSQL) and interactive React dashboard.
6. Demonstrate measurable improvement over a naive rolling-average baseline.

---

## 4. System Architecture

The system is organized into four distinct layers:

```
[ ML Pipeline ]  →  [ PostgreSQL DB ]  →  [ FastAPI Backend ]  →  [ React Frontend ]
   src/                 inventory_db          backend/                frontend/
```

**Layer 1 — ML Pipeline (src/)**
- `generate_data.py` — Synthetic retail dataset generation with trend, seasonality, and noise
- `data_pipeline.py` — Feature engineering: lag features, rolling statistics, calendar encodings
- `forecasting.py` — XGBoost model training, walk-forward CV, future forecast generation
- `inventory_optimization.py` — EOQ, safety stock, reorder point, ABC-XYZ segmentation
- `run_pipeline.py` — Master runner executing all steps in sequence

**Layer 2 — Database (PostgreSQL)**
- Four tables: `sales_data`, `forecasts`, `inventory_policy`, `model_metrics`
- Managed via SQLAlchemy ORM; populated from ML pipeline CSV outputs via `load_db.py`

**Layer 3 — REST API (backend/)**
- FastAPI application with three route groups: `/forecasts`, `/inventory`, `/metrics`
- Pydantic schemas for request/response validation
- CORS enabled for React frontend communication
- Auto-generated Swagger documentation at `/docs`

**Layer 4 — Dashboard (frontend/)**
- React 18 with React Router for client-side navigation
- TanStack Query for server state management and caching
- Recharts for interactive data visualization
- Tailwind CSS for responsive dark-theme UI

---

## 5. Dataset Description

A realistic synthetic retail dataset was generated to simulate 3 years of daily sales (2022–2024) across 8 SKUs and 3 store locations.

| Attribute        | Details                                                      |
|------------------|--------------------------------------------------------------|
| Total Records    | 26,304 rows                                                  |
| SKUs             | 8 (Laptop, Headphones, T-Shirt, Sneakers, Coffee Maker, Desk Chair, Notebook, Water Bottle) |
| Categories       | Electronics, Apparel, Appliances, Furniture, Stationery, Accessories |
| Stores           | 3 (Store A, Store B, Store C)                               |
| Date Range       | January 1, 2022 — December 31, 2024                         |
| Price Range      | $5 (Notebook) to $800 (Laptop)                              |
| Lead Times       | 2–10 days depending on SKU                                   |

**Demand generation formula:**

```
demand(t) = base_demand × (1 + 0.0003t)          [trend]
           + base × 0.15 × sin(2π × t / 7)        [weekly seasonality]
           + base × 0.25 × sin(2π × t / 365)      [annual seasonality]
           + Normal(0, base × 0.1)                 [noise]
```

**Multipliers applied:**
- Holiday effect: ×1.8
- Weekend effect: ×1.2
- Promotional event (5% probability): ×1.5

The dataset was then aggregated to weekly frequency (3,792 rows) for model training, as weekly demand is the standard planning horizon in retail inventory management.

---

## 6. Methodology

### 6.1 Feature Engineering

Features were constructed to give the model information about temporal patterns and recent demand behavior without leaking future values:

**Lag Features** — Capture recent demand memory:
- `lag_7`, `lag_14`, `lag_21`, `lag_28` (demand from 1, 2, 3, 4 weeks ago)

**Rolling Statistics** — Capture local trend and volatility:
- Rolling mean over 7, 14, 30-day windows (shifted by 1 to prevent leakage)
- Rolling standard deviation over 7, 14-day windows

**Calendar Features** — Capture seasonality:
- Week of year, month, quarter, day of year
- Sine and cosine encodings of month and day-of-week (to capture cyclicality smoothly)

**Event Flags:**
- `is_holiday`, `is_weekend`, `is_promo` (binary indicators)

Total feature count: **20 features** per observation.

### 6.2 Model Selection — XGBoost

XGBoost (Extreme Gradient Boosting) was selected for the following reasons:

- **Handles tabular features natively:** Unlike ARIMA which models a univariate series, XGBoost treats the forecasting problem as supervised regression, using all engineered features simultaneously.
- **Scales across SKUs:** A single model architecture applies to all SKU-Store combinations without manual parameter tuning per series.
- **Feature importance:** Provides interpretable feature importance scores, enabling business understanding of demand drivers.
- **Speed:** Trains in seconds on the dataset size used.

**Model configuration:**
```
n_estimators   = 300
learning_rate  = 0.05
max_depth      = 5
subsample      = 0.8
colsample_bytree = 0.8
```

A baseline model (4-week rolling average) was implemented for comparison.

### 6.3 Walk-Forward Cross-Validation

Standard random train-test splitting is **invalid** for time series — it leaks future data into training, artificially inflating accuracy. Walk-forward cross-validation was implemented instead:

```
Fold 1:  Train [week 1 → week N-8]   Test [week N-7 → week N-4]
Fold 2:  Train [week 1 → week N-4]   Test [week N-3 → week N]
Fold 3:  Train [week 1 → week N]     Test [next 4 weeks]
```

Each fold trains strictly on past data and evaluates on unseen future weeks. SMAPE scores are averaged across 3 folds per SKU-Store model.

### 6.4 Evaluation Metrics

| Metric | Formula | Why used |
|--------|---------|----------|
| MAPE   | mean(\|actual - pred\| / actual) × 100 | Percentage error, interpretable |
| SMAPE  | mean(\|actual - pred\| / ((actual + pred)/2)) × 100 | Symmetric, handles near-zero values |
| RMSE   | √(mean((actual - pred)²)) | Penalizes large errors |
| Bias   | mean(pred - actual) | Detects systematic over/under-forecasting |

---

## 7. Inventory Optimization

### 7.1 Economic Order Quantity (EOQ)

EOQ determines the optimal order size that minimizes the sum of ordering cost and inventory holding cost:

```
EOQ = √(2 × D × S / H)

Where:
  D = Annual demand (units)
  S = Ordering cost per order ($50 assumed)
  H = Annual holding cost per unit (price × 25% holding rate)
```

EOQ is computed per SKU using the annual demand derived from the weekly forecast aggregated over 52 weeks.

### 7.2 Safety Stock

Safety stock provides a buffer against demand uncertainty during lead time:

```
Safety Stock = Z × σ_d × √(lead_time_weeks)

Where:
  Z     = 1.645 (z-score for 95% service level)
  σ_d   = Standard deviation of weekly demand
  lead_time_weeks = supplier lead time in weeks
```

A 95% service level was chosen as the default, meaning the system is designed to prevent stockouts in 95 out of every 100 replenishment cycles.

### 7.3 Reorder Point

The reorder point triggers a purchase order when inventory hits this level:

```
Reorder Point = (avg_weekly_demand × lead_time_weeks) + safety_stock
```

This ensures that even if demand runs at average levels during the lead time, plus a safety buffer, stock does not run out before the new order arrives.

### 7.4 Stockout Probability

Stockout probability quantifies the risk of running out of stock given current inventory levels:

```
P(stockout) = 1 - Φ((current_inventory - μ_lt) / σ_lt)

Where:
  μ_lt = avg_demand × lead_time_weeks      (expected demand during lead time)
  σ_lt = σ_demand × √(lead_time_weeks)    (std dev of demand during lead time)
  Φ    = Normal CDF
```

This gives a concrete business metric: "There is a 42% probability this item will stock out before the next order arrives."

### 7.5 ABC-XYZ Segmentation

**ABC Classification** (by annual revenue contribution):
- **A items:** Top 70% of revenue — highest priority, tight control, frequent orders
- **B items:** Next 20% of revenue — moderate control
- **C items:** Bottom 10% of revenue — periodic review, bulk ordering

**XYZ Classification** (by demand variability, measured by Coefficient of Variation = σ/μ):
- **X items:** CoV < 0.5 — stable, predictable demand — easy to forecast
- **Y items:** CoV 0.5–1.0 — moderately variable demand
- **Z items:** CoV > 1.0 — highly erratic demand — needs safety stock buffer

Combined segments (e.g., AX = high revenue + stable demand) drive differentiated inventory strategies.

---

## 8. Results & Evaluation

### 8.1 Forecast Accuracy

| Metric              | Value     |
|---------------------|-----------|
| Avg MAPE            | **7.79%** |
| Avg CV-SMAPE        | **7.86%** |
| Baseline SMAPE (avg)| 18.51%    |
| Improvement vs Baseline | **+10.65% SMAPE** |
| Total models trained | 24 (8 SKUs × 3 stores) |

**Best performing model:** SKU_005 (Coffee Maker) — Store A with MAPE = 6.66%  
**Most challenging model:** SKU_008 (Water Bottle) — Store A with MAPE = 8.76%

All models were trained in under 60 seconds total on a standard laptop (Python 3.13, XGBoost 3.2).

### 8.2 Per-SKU MAPE Summary

| SKU        | Product     | Avg MAPE (3 stores) |
|------------|-------------|----------------------|
| SKU_001    | Laptop       | 8.18%               |
| SKU_002    | Headphones   | 7.94%               |
| SKU_003    | T-Shirt      | 7.81%               |
| SKU_004    | Sneakers     | 7.63%               |
| SKU_005    | Coffee Maker | 7.44%               |
| SKU_006    | Desk Chair   | 7.75%               |
| SKU_007    | Notebook     | 7.44%               |
| SKU_008    | Water Bottle | 8.11%               |

### 8.3 Inventory Policy Results

| Metric                              | Value  |
|-------------------------------------|--------|
| SKU-Store pairs analyzed            | 24     |
| Reorder alerts generated            | 8      |
| High-risk items (stockout > 30%)    | 4      |
| Service level target                | 95%    |
| Ordering cost assumption            | $50    |
| Holding cost rate                   | 25%/yr |

### 8.4 What-If Simulation Capability

The system supports real-time scenario modeling. Example: applying a +30% demand shock to SKU_001 (Laptop) at Store_A increases the reorder point by approximately 23 units and the safety stock by 18 units, while raising the EOQ by 14%, demonstrating how the system quantifies the inventory impact of demand uncertainty.

---

## 9. Dashboard Features

The React dashboard provides 7 interactive pages accessible via a persistent sidebar:

| Page                 | Key Features                                                               |
|----------------------|----------------------------------------------------------------------------|
| **Overview**         | KPI cards (MAPE, alerts, stores, SKUs), weekly sales trend, revenue pie chart |
| **Demand Forecast**  | Per-SKU/store chart with actual history + 8-week XGBoost forecast + baseline |
| **Inventory Policy** | Filterable table: EOQ, safety stock, reorder point, stockout risk, segment |
| **Reorder Alerts**   | Prioritized alert cards (Critical/High/Medium) with order quantity recommendations |
| **ABC-XYZ**          | Revenue vs. volatility scatter plot, segment strategy table                |
| **Model Performance**| MAPE histogram, RMSE scatter, sortable full metrics table                  |
| **What-If Simulator**| Sliders for demand shock, service level, ordering cost; live policy recalculation |

The API exposes 9 REST endpoints with auto-generated Swagger documentation, enabling easy integration with external ERP or WMS systems.

---

## 10. Conclusion & Future Work

This project demonstrates a complete, production-structured AI system that addresses a real business problem in retail supply chain management. The XGBoost forecasting pipeline achieves 7.79% MAPE with proper time-series validation, representing a 10.65% improvement over naive baseline methods. The inventory optimization engine translates these forecasts into concrete, mathematically grounded ordering policies.

**Key contributions:**
- Walk-forward cross-validation prevents data leakage, ensuring honest accuracy reporting
- Stockout probability provides a risk-based framing that business stakeholders can act on
- ABC-XYZ segmentation enables differentiated inventory strategies rather than one-size-fits-all policies
- The full-stack architecture (FastAPI + PostgreSQL + React) demonstrates production readiness beyond a Jupyter notebook

**Future enhancements:**

1. **Real data integration** — Connect to public datasets (Walmart M5 Competition, Kaggle Store Item Demand) or enterprise ERP systems via API
2. **Prophet or LSTM ensemble** — Add Meta Prophet for strong seasonality modeling or a Temporal Fusion Transformer for long-range dependencies
3. **Automated retraining** — Implement drift detection (Population Stability Index) to trigger model retraining when demand patterns shift
4. **Multi-echelon inventory** — Extend from store-level to warehouse + store hierarchy optimization
5. **Price elasticity modeling** — Incorporate price as a demand driver to enable promotional planning
6. **MLflow integration** — Add experiment tracking and model registry for full MLOps lifecycle management

---

## 11. References

1. Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). *The M4 Competition: 100,000 time series and 61 forecasting methods.* International Journal of Forecasting, 36(1), 54–74.

2. Chen, T., & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System.* Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining.

3. Silver, E. A., Pyke, D. F., & Thomas, D. J. (2017). *Inventory and Production Management in Supply Chains* (4th ed.). CRC Press.

4. Wilson, R. H. (1934). *A Scientific Routine for Stock Control.* Harvard Business Review, 13, 116–128. [Original EOQ paper]

5. Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts. https://otexts.com/fpp3/

6. FastAPI Documentation. (2024). https://fastapi.tiangolo.com/

7. XGBoost Documentation. (2024). https://xgboost.readthedocs.io/

8. Recharts Library. (2024). https://recharts.org/

9. Walmart M5 Forecasting Competition. (2020). Kaggle. https://www.kaggle.com/c/m5-forecasting-accuracy

10. Syntetos, A. A., Boylan, J. E., & Croston, J. D. (2005). *On the categorization of demand patterns.* Journal of the Operational Research Society, 56(5), 495–503. [ABC-XYZ segmentation foundation]

---

*Report prepared for portfolio submission. Project source code available on GitHub.*  
*Built with: Python 3.13 · XGBoost 3.2 · FastAPI 0.135 · React 18 · PostgreSQL 18*
