from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base
from routes import forecasts, inventory, metrics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Demand Forecasting & Inventory Optimization API",
    description="REST API for retail demand forecasting and inventory policy optimization using XGBoost.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecasts.router)
app.include_router(inventory.router)
app.include_router(metrics.router)


@app.get("/")
def root():
    return {
        "message": "AI Demand Forecasting & Inventory Optimization API",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
